# Configuração do Webhook na Z-API

## Status Atual

O servidor está rodando e funcionando perfeitamente. A URL pública está ativa e pronta para receber mensagens do WhatsApp.

## URL do Webhook

```
https://8000-itwrjh3ziag1rpg05i6tg-5d2189a8.us2.manus.computer/webhook
```

## Como Configurar na Z-API

### Opção 1: Via Painel Admin (Recomendado)

1. Acesse https://painel.z-api.io
2. Faça login com suas credenciais
3. Clique em "Instâncias"
4. Procure pela instância com ID: `3F0FAB88697C1334BAEE06BC27EA9655`
5. Clique no ícone de "visualizar" (olho)
6. Clique nos 3 pontinhos e escolha "Editar"
7. Procure pela seção "Webhooks"
8. Cole a URL do webhook no campo "Webhook de Recebimento":
   ```
   https://8000-itwrjh3ziag1rpg05i6tg-5d2189a8.us2.manus.computer/webhook
   ```
9. Salve as alterações

### Opção 2: Via API (Requer Client-Token)

Se você tiver o **Client-Token** (token de segurança da conta, diferente do token da instância):

```bash
curl -X PUT "https://api.z-api.io/instances/3F0FAB88697C1334BAEE06BC27EA9655/token/F61D1B842157E39051047569/update-webhook-received" \
  -H "Content-Type: application/json" \
  -H "Client-Token: SEU_CLIENT_TOKEN_AQUI" \
  -d '{"value": "https://8000-itwrjh3ziag1rpg05i6tg-5d2189a8.us2.manus.computer/webhook"}'
```

## Testando o Webhook

Depois de configurar, você pode testar enviando uma mensagem para o número conectado na Z-API. O servidor responderá automaticamente com uma mensagem gerada pela IA.

### Teste Local (sem Z-API)

Para testar sem precisar enviar uma mensagem real pelo WhatsApp:

```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{"phone": "5511999999999", "message": "Olá, quero saber sobre a mentoria"}'
```

## Logs

Os logs do servidor estão em:
```
/home/ubuntu/arcaamed-agent/agent.log
```

Para monitorar em tempo real:
```bash
tail -f /home/ubuntu/arcaamed-agent/agent.log
```

## Endpoints Disponíveis

- `GET /` - Health check
- `GET /health` - Status do servidor
- `POST /webhook` - Recebe mensagens do Z-API
- `POST /webhook/status` - Recebe atualizações de status
- `POST /test` - Testa o agente localmente
- `GET /conversations` - Lista conversas ativas (debug)

