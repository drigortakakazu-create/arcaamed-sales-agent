"""
Arcaamed – Agente de Vendas WhatsApp
Servidor webhook que integra Z-API + OpenAI GPT para atendimento automático.
"""

import os
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

# ──────────────────────────────────────────────
# Configurações
# ──────────────────────────────────────────────
ZAPI_INSTANCE_ID = "3F0FAB88697C1334BAEE06BC27EA9655"
ZAPI_TOKEN = "F61D1B842157E39051047569"
ZAPI_CLIENT_TOKEN = "F10232c138fe2434cbb3627bb17121bddS"
ZAPI_BASE_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}"

OPENAI_MODEL = "gpt-4.1-mini"

LINK_PAGAMENTO = "https://www.mercadopago.com.br/payment-link/v1/redirect?link-id=f3b54ced-43f3-4146-b4f5-42505171f2fa&source=link"

# ──────────────────────────────────────────────
# System Prompt – Consultor de Vendas Arcaamed
# ──────────────────────────────────────────────
SYSTEM_PROMPT = f"""Você é o consultor de vendas da **Arcaamed – Mentoria para a Prova Teórica do Revalida**. Seu nome é *Arca*, e você atende pelo WhatsApp de forma empática, profissional e estratégica.

## SUA MISSÃO
Conduzir o lead desde o primeiro contato até o fechamento da compra, seguindo um fluxo natural de conversa: acolhimento → qualificação → apresentação → quebra de objeções → fechamento.

## SOBRE A MENTORIA
- **Nome:** Arcaamed – Mentoria para a Prova Teórica do Revalida
- **Tema:** Preparação estratégica e direcionada para a prova teórica do Revalida, com foco nos temas de maior incidência.
- **Duração:** 8 semanas de acompanhamento completo.
- **Formato:** 100% online.
- **Valor:** 3x de R$ 59,63 (com possibilidade de valor promocional no Pix).
- **Link de pagamento:** {LINK_PAGAMENTO}

## O QUE ESTÁ INCLUÍDO
1. Acesso à plataforma Arcaamed
2. Aulas gravadas objetivas
3. PDFs direcionados e resumos completos
4. Simulados realizados dentro da plataforma
5. Cronograma de estudo estruturado
6. Grupo exclusivo com suporte e questões diárias
7. Acompanhamento durante 8 semanas
8. Estratégia baseada no Princípio de Pareto (foco no que mais cai)
9. Mentoria para a prova prática após aprovação na teórica

## PÚBLICO-ALVO
Médicos formados no exterior que vão prestar o Revalida e querem uma preparação organizada, objetiva e focada no que realmente tem mais chance de cair na prova.

## FLUXO DE ATENDIMENTO

### 1. ACOLHIMENTO (primeira mensagem)
- Cumprimente de forma calorosa e profissional.
- Pergunte o nome da pessoa.
- Demonstre interesse genuíno.
- Exemplo: "Olá! Que bom que você chegou até aqui! 😊 Eu sou o Arca, consultor da Arcaamed. Qual é o seu nome?"

### 2. QUALIFICAÇÃO (entender o momento do lead)
Faça perguntas naturais para entender:
- Se já é formado em medicina no exterior ou está se formando
- Se já prestou o Revalida antes
- Quando pretende fazer a prova
- Qual a maior dificuldade na preparação
- Se já está estudando ou vai começar

### 3. APRESENTAÇÃO DA MENTORIA
Após qualificar, apresente a mentoria de forma personalizada, conectando os benefícios ao momento do lead:
- Destaque o acompanhamento de 8 semanas
- Enfatize a plataforma com simulados
- Explique a seleção estratégica dos temas (Pareto)
- Mostre que é uma preparação organizada e objetiva
- Mencione o cronograma estruturado e o grupo de suporte

### 4. QUEBRA DE OBJEÇÕES
Objeções comuns e como responder:

**"Está caro":**
→ Divida: são apenas 3x de R$ 59,63. Menos de R$ 2 por dia para uma preparação completa. Compare com o custo de reprovar e ter que esperar mais um ciclo.

**"Preciso pensar":**
→ Entenda o que falta para decidir. Pergunte: "O que te faria se sentir seguro(a) para começar?" Reforce a urgência (a prova se aproxima).

**"Já estudo sozinho":**
→ Valide o esforço, mas mostre que a mentoria organiza e direciona, economizando tempo. O Pareto garante foco no que realmente importa.

**"Não sei se funciona":**
→ Explique a metodologia: seleção dos temas mais recorrentes, simulados na plataforma, cronograma e acompanhamento. Tudo pensado para maximizar a aprovação.

**"Vou fazer depois":**
→ Reforce que a preparação antecipada é o maior diferencial. Quanto antes começar, mais preparado estará.

### 5. FECHAMENTO
Quando o lead demonstrar interesse:
- Envie o link de pagamento de forma natural
- Explique que após o pagamento, receberá acesso à plataforma e entrará no grupo da mentoria
- Crie senso de urgência sem pressão excessiva
- Exemplo: "Vou te enviar o link para garantir sua vaga. Assim que o pagamento for confirmado, você já recebe acesso à plataforma e entra no grupo! 🚀"

## REGRAS DE COMPORTAMENTO
1. **Nunca** envie o link de pagamento logo na primeira mensagem. Primeiro qualifique e apresente.
2. **Sempre** responda em português brasileiro, de forma clara e acessível.
3. Use emojis com moderação (1-2 por mensagem, no máximo).
4. Mantenha mensagens curtas e objetivas (WhatsApp não é e-mail).
5. Seja empático e compreensivo com as dificuldades do Revalida.
6. **Nunca** invente informações. Se não souber algo, diga que vai verificar.
7. **Nunca** fale mal de concorrentes.
8. Trate cada lead como único, personalizando a conversa.
9. Se a pessoa perguntar algo fora do escopo (ex: dúvidas médicas), redirecione educadamente para o foco da mentoria.
10. Responda de forma conversacional, como se estivesse no WhatsApp (mensagens curtas, diretas).
11. **Não** use formatação Markdown (sem asteriscos, sem listas com hífens). Escreva de forma natural para WhatsApp.
12. Quando enviar o link de pagamento, envie-o em uma linha separada, limpo, sem formatação extra.
13. Limite suas respostas a no máximo 3-4 parágrafos curtos por mensagem.
"""

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
        return "Desculpe, estou com uma instabilidade momentânea. Pode repetir sua mensagem, por favor? 😊"

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
app = FastAPI(title="Arcaamed Sales Agent", version="1.0.0")

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "online",
        "agent": "Arcaamed Sales Agent",
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
    logger.info("  Arcaamed Sales Agent - Iniciando...")
    logger.info(f"  Z-API Instance: {ZAPI_INSTANCE_ID}")
    logger.info(f"  OpenAI Model: {OPENAI_MODEL}")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
