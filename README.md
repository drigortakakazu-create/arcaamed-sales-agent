# Arcaamed Sales Agent

Agente de vendas automático para WhatsApp que integra Z-API com OpenAI GPT. O agente qualifica leads, quebra objeções e conduz ao fechamento da venda da mentoria Arcaamed.

## Características

- **Integração Z-API:** Recebe mensagens do WhatsApp via webhook
- **IA Conversacional:** Usa OpenAI GPT-4 mini para gerar respostas naturais
- **Histórico de Conversa:** Mantém contexto entre mensagens por número de telefone
- **Fluxo de Vendas Completo:** Acolhimento → Qualificação → Apresentação → Objeções → Fechamento
- **Deploy Automático:** Pronto para Render.com com Procfile

## Pré-requisitos

- Python 3.9+
- Conta Z-API com instância configurada
- Chave de API OpenAI
- Conta Render.com (para deploy)

## Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/drigortakakazu-create/arcaamed-sales-agent.git
cd arcaamed-sales-agent
```

2. Crie um arquivo `.env` baseado em `.env.example`:
```bash
cp .env.example .env
```

3. Configure as variáveis de ambiente no arquivo `.env`:
```
OPENAI_API_KEY=sua_chave_openai
ZAPI_INSTANCE_ID=seu_instance_id
ZAPI_TOKEN=seu_token
ZAPI_CLIENT_TOKEN=seu_client_token
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Execute o servidor:
```bash
python main.py
```

O servidor iniciará em `http://localhost:8000`

## Variáveis de Ambiente

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| `OPENAI_API_KEY` | Chave de API da OpenAI | ✅ Sim |
| `OPENAI_MODEL` | Modelo OpenAI (padrão: gpt-4.1-mini) | ❌ Não |
| `ZAPI_INSTANCE_ID` | ID da instância Z-API | ✅ Sim |
| `ZAPI_TOKEN` | Token da instância Z-API | ✅ Sim |
| `ZAPI_CLIENT_TOKEN` | Token de segurança da conta Z-API | ✅ Sim |
| `AGENT_NAME` | Nome da agente (padrão: Clara) | ❌ Não |
| `AGENT_ROLE` | Papel da agente no prompt | ❌ Não |
| `LINK_PAGAMENTO` | Link oficial de fechamento | ❌ Não |
| `PORT` | Porta do servidor (padrão: 8000) | ❌ Não |

## Endpoints

- `GET /` - Health check
- `GET /health` - Status do servidor
- `POST /webhook` - Recebe mensagens do Z-API
- `POST /webhook/status` - Recebe atualizações de status
- `POST /test` - Testa o agente localmente
- `GET /conversations` - Lista conversas ativas (debug)

## Configuração do Webhook na Z-API

1. Acesse o painel da Z-API em https://painel.z-api.io
2. Vá em **Instâncias** e selecione sua instância
3. Clique em **Editar** (nos 3 pontinhos)
4. Na seção **Webhooks**, configure:
   - **Webhook de Recebimento:** `https://seu-dominio.onrender.com/webhook`
   - **Webhook de Status:** `https://seu-dominio.onrender.com/webhook/status`

## Deploy no Render

### Opção 1: Deploy via GitHub (Recomendado)

1. Acesse https://render.com
2. Clique em **New +** → **Web Service**
3. Selecione **Connect a repository** e escolha este repositório
4. Configure:
   - **Name:** arcaamed-sales-agent
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Adicione as variáveis de ambiente:
   - `OPENAI_API_KEY`
   - `ZAPI_INSTANCE_ID`
   - `ZAPI_TOKEN`
   - `ZAPI_CLIENT_TOKEN`
6. Clique em **Deploy**

### Opção 2: Deploy via render.yaml

Se usar o arquivo `render.yaml`, o Render detectará automaticamente as configurações.

## Testando o Agente

### Teste Local

```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{"phone": "5511999999999", "message": "Olá, quero saber sobre a mentoria"}'
```

### Teste via Webhook

```bash
curl -X POST "https://seu-dominio.onrender.com/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "fromMe": false,
    "text": {"message": "Olá, quero saber sobre a mentoria"},
    "senderName": "Teste User",
    "instanceId": "sua_instance_id"
  }'
```

## Estrutura do Projeto

```
arcaamed-sales-agent/
├── agent_config.py         # Persona, conhecimento e políticas do agente
├── main.py                 # Servidor FastAPI principal
├── requirements.txt        # Dependências Python
├── Procfile               # Configuração para Render
├── render.yaml            # Configuração alternativa para Render
├── .env.example           # Exemplo de variáveis de ambiente
├── README.md              # Este arquivo
├── WEBHOOK_SETUP.md       # Instruções de configuração do webhook
├── DEPLOYMENT.md          # Guia de deployment
└── agent.log              # Log de execução (gerado em runtime)
```

## Fluxo de Vendas

O agente segue um fluxo estruturado de vendas:

1. **Acolhimento:** Cumprimento caloroso e apresentação
2. **Qualificação:** Entender o momento do lead (formação, timing, dificuldades)
3. **Apresentação:** Apresentar a mentoria com foco nos benefícios
4. **Quebra de Objeções:** Responder objeções comuns (preço, eficácia, tempo)
5. **Fechamento:** Enviar link de pagamento quando o lead demonstra interesse

## Logs

Os logs são salvos em `agent.log` e também exibidos no console. Monitore em tempo real:

```bash
tail -f agent.log
```

## Troubleshooting

### Erro: "OPENAI_API_KEY not found"
Certifique-se de que a variável de ambiente está configurada no Render.

### Erro: "your client-token is not configured"
Verifique se o `ZAPI_CLIENT_TOKEN` está correto e configurado.

### Mensagens não são enviadas
1. Verifique se o webhook está configurado corretamente na Z-API
2. Confira os logs para erros de envio
3. Teste o endpoint `/test` para verificar se a IA está respondendo

## Suporte

Para problemas ou dúvidas, verifique os logs e a documentação em `WEBHOOK_SETUP.md` e `DEPLOYMENT.md`.

## Licença

Este projeto é propriedade da Arcaamed.

## Autor

Desenvolvido com ❤️ para Arcaamed - Mentoria para o Revalida
