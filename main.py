"""
Arcaamed – Agente de Vendas WhatsApp
Servidor webhook que integra Z-API + OpenAI GPT para atendimento automático.
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from openai import OpenAI
from agent_config import (
    OPENAI_MODEL,
    ESCALATION_KEYWORDS,
    AGENT_NAME,
    build_system_prompt,
)

# ──────────────────────────────────────────────
# Configurações
# ──────────────────────────────────────────────
import os

ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID", "")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN", "")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN", "")
ZAPI_BASE_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}"
SYSTEM_PROMPT = build_system_prompt()

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("arcaamed")

# ──────────────────────────────────────────────
# Clientes
# ──────────────────────────────────────────────
openai_client = OpenAI()  # usa OPENAI_API_KEY do ambiente
http_client = httpx.Client(timeout=30)

# ──────────────────────────────────────────────
# Histórico de conversas (em memória)
# ──────────────────────────────────────────────
conversations: Dict[str, List[dict]] = {}
MAX_HISTORY = 40  # máximo de mensagens no histórico por conversa

def get_conversation(phone: str) -> List[dict]:
    """Retorna o histórico de conversa de um número."""
    if phone not in conversations:
        conversations[phone] = []
    return conversations[phone]

def add_message(phone: str, role: str, content: str):
    """Adiciona mensagem ao histórico."""
    conv = get_conversation(phone)
    conv.append({"role": role, "content": content})
    # Manter apenas as últimas MAX_HISTORY mensagens
    if len(conv) > MAX_HISTORY:
        conversations[phone] = conv[-MAX_HISTORY:]

# ──────────────────────────────────────────────
# OpenAI – Gerar resposta
# ──────────────────────────────────────────────
def generate_response(phone: str, user_message: str) -> str:
    """Gera resposta usando GPT com histórico de conversa."""
    add_message(phone, "user", user_message)

    lowered = user_message.lower()
    if any(keyword in lowered for keyword in ESCALATION_KEYWORDS):
        handoff_message = (
            "Perfeito, te encaminho para atendimento humano agora. "
            "Se puder, me passe seu nome e principal dúvida para eu agilizar por aqui."
        )
        add_message(phone, "assistant", handoff_message)
        return handoff_message

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(get_conversation(phone))

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        assistant_message = response.choices[0].message.content.strip()
        add_message(phone, "assistant", assistant_message)
        logger.info(f"[GPT] Resposta gerada para {phone}: {assistant_message[:80]}...")
        return assistant_message
    except Exception as e:
        logger.error(f"[GPT] Erro ao gerar resposta: {e}")
        return (
            f"Desculpa, aqui é a {AGENT_NAME}. Tive uma instabilidade agora, "
            "mas sigo com você. Pode repetir sua mensagem em uma frase?"
        )

# ──────────────────────────────────────────────
# Z-API – Enviar mensagem
# ──────────────────────────────────────────────
def send_whatsapp_message(phone: str, message: str) -> bool:
    """Envia mensagem via Z-API."""
    url = f"{ZAPI_BASE_URL}/send-text"
    payload = {
        "phone": phone,
        "message": message,
    }
    headers = {
        "Content-Type": "application/json",
        "Client-Token": ZAPI_CLIENT_TOKEN,
    }

    try:
        response = http_client.post(url, json=payload, headers=headers)
        logger.info(f"[Z-API] Mensagem enviada para {phone} | Status: {response.status_code}")
        logger.info(f"[Z-API] Resposta: {response.text}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"[Z-API] Erro ao enviar mensagem: {e}")
        return False

# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────
app = FastAPI(title="Arcaamed Sales Agent", version="2.0.0")

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "online",
        "agent": "Arcaamed Sales Agent",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "active_conversations": len(conversations),
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(request: Request):
    """
    Recebe mensagens do Z-API (webhook).
    Processa apenas mensagens de texto recebidas.
    """
    try:
        body = await request.json()
        logger.info(f"[Webhook] Payload recebido: {json.dumps(body, ensure_ascii=False)[:500]}")

        # Verificar se é uma mensagem recebida (não enviada por nós)
        is_from_me = body.get("fromMe", False)
        if is_from_me:
            logger.info("[Webhook] Mensagem enviada por nós, ignorando.")
            return JSONResponse(content={"status": "ignored", "reason": "fromMe"})

        # Extrair informações da mensagem
        # Z-API pode enviar em diferentes formatos
        phone = body.get("phone")
        message_text = None

        # Tentar extrair texto da mensagem
        # Formato padrão Z-API
        if "text" in body and body["text"]:
            if isinstance(body["text"], dict):
                message_text = body["text"].get("message", "")
            else:
                message_text = str(body["text"])
        elif "message" in body:
            if isinstance(body["message"], dict):
                message_text = body["message"].get("body", "") or body["message"].get("text", "")
            else:
                message_text = str(body["message"])
        elif "body" in body:
            message_text = str(body["body"])

        # Também verificar campo 'text.message' para formato Z-API v2
        if not message_text and "text" in body and isinstance(body["text"], dict):
            message_text = body["text"].get("message", "")

        if not phone:
            logger.warning("[Webhook] Sem número de telefone no payload.")
            return JSONResponse(content={"status": "error", "reason": "no phone"})

        if not message_text or not message_text.strip():
            logger.info(f"[Webhook] Mensagem sem texto de {phone}, ignorando (pode ser mídia).")
            return JSONResponse(content={"status": "ignored", "reason": "no text"})

        message_text = message_text.strip()
        logger.info(f"[Webhook] Mensagem de {phone}: {message_text}")

        # Gerar resposta com IA
        ai_response = generate_response(phone, message_text)

        # Enviar resposta via Z-API
        sent = send_whatsapp_message(phone, ai_response)

        return JSONResponse(content={
            "status": "success" if sent else "send_failed",
            "phone": phone,
            "response_preview": ai_response[:100],
        })

    except Exception as e:
        logger.error(f"[Webhook] Erro ao processar: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)},
        )

@app.post("/webhook/status")
async def webhook_status(request: Request):
    """Recebe atualizações de status de mensagens da Z-API."""
    try:
        body = await request.json()
        logger.info(f"[Status] {json.dumps(body, ensure_ascii=False)[:300]}")
        return JSONResponse(content={"status": "received"})
    except Exception as e:
        logger.error(f"[Status] Erro: {e}")
        return JSONResponse(content={"status": "error"})

@app.get("/conversations")
async def list_conversations():
    """Lista conversas ativas (para debug)."""
    summary = {}
    for phone, msgs in conversations.items():
        summary[phone] = {
            "total_messages": len(msgs),
            "last_message": msgs[-1]["content"][:80] if msgs else "",
            "last_role": msgs[-1]["role"] if msgs else "",
        }
    return summary

@app.post("/test")
async def test_message(request: Request):
    """Endpoint de teste: simula uma mensagem recebida."""
    body = await request.json()
    phone = body.get("phone", "5511999999999")
    message = body.get("message", "Olá, quero saber sobre a mentoria")

    ai_response = generate_response(phone, message)

    return {
        "phone": phone,
        "user_message": message,
        "ai_response": ai_response,
    }

# ──────────────────────────────────────────────
# Inicialização
# ──────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  Arcaamed Sales Agent v2.0 - Iniciando...")
    logger.info(f"  Z-API Instance: {ZAPI_INSTANCE_ID}")
    logger.info(f"  OpenAI Model: {OPENAI_MODEL}")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
