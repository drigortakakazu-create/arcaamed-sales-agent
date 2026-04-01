# Deployment e Manutenção do Agente Arcaamed

## Iniciando o Servidor

### Opção 1: Execução Manual

```bash
cd /home/ubuntu/arcaamed-agent
python3 main.py
```

O servidor iniciará na porta 8000 (localhost:8000).

### Opção 2: Execução em Background (nohup)

```bash
cd /home/ubuntu/arcaamed-agent
nohup python3 main.py > server.log 2>&1 &
```

### Opção 3: Usando systemd (Recomendado para Produção)

Criar arquivo `/etc/systemd/system/arcaamed-agent.service`:

```ini
[Unit]
Description=Arcaamed Sales Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/arcaamed-agent
ExecStart=/usr/bin/python3 /home/ubuntu/arcaamed-agent/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Depois executar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable arcaamed-agent
sudo systemctl start arcaamed-agent
```

## Verificando Status

```bash
# Verificar se o servidor está rodando
curl http://localhost:8000/

# Ver logs em tempo real
tail -f /home/ubuntu/arcaamed-agent/agent.log

# Listar processo
ps aux | grep "python3 main.py"
```

## Parando o Servidor

```bash
# Se estiver em background
kill <PID>

# Se estiver usando systemd
sudo systemctl stop arcaamed-agent
```

## Variáveis de Ambiente Necessárias

O servidor usa a variável `OPENAI_API_KEY` que já está configurada no ambiente.

Se precisar reconfigurar:

```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

## Monitoramento

### Logs Importantes

- **Arquivo de log:** `/home/ubuntu/arcaamed-agent/agent.log`
- **Servidor:** Rodando na porta 8000
- **URL Pública:** `https://8000-itwrjh3ziag1rpg05i6tg-5d2189a8.us2.manus.computer`

### Métricas Úteis

```bash
# Ver número de conversas ativas
curl http://localhost:8000/conversations | python3 -m json.tool

# Testar agente
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{"phone": "5511999999999", "message": "Olá"}'
```

## Troubleshooting

### Erro: "Port 8000 already in use"

```bash
# Encontrar processo usando a porta
lsof -i :8000

# Matar o processo
kill -9 <PID>
```

### Erro: "OPENAI_API_KEY not found"

```bash
# Verificar se a variável está configurada
echo $OPENAI_API_KEY

# Se não estiver, configurar
export OPENAI_API_KEY="sua-chave-aqui"
```

### Servidor não responde

```bash
# Reiniciar o servidor
kill <PID>
cd /home/ubuntu/arcaamed-agent
nohup python3 main.py > server.log 2>&1 &
```

## Backup e Recuperação

### Backup dos Logs

```bash
cp /home/ubuntu/arcaamed-agent/agent.log /home/ubuntu/arcaamed-agent/agent.log.backup
```

### Restaurar Configuração

Todos os arquivos estão em `/home/ubuntu/arcaamed-agent/`. Para restaurar:

```bash
cd /home/ubuntu/arcaamed-agent
git clone <repo-url> .
```

## Atualizando o Agente

Para atualizar o código:

1. Parar o servidor
2. Atualizar os arquivos
3. Reiniciar o servidor

```bash
kill <PID>
# ... atualizar arquivos ...
cd /home/ubuntu/arcaamed-agent
nohup python3 main.py > server.log 2>&1 &
```

## Estrutura de Diretórios

```
/home/ubuntu/arcaamed-agent/
├── main.py                 # Servidor principal
├── agent.log              # Logs de execução
├── server.log             # Logs do servidor
├── WEBHOOK_SETUP.md       # Instruções de configuração
├── DEPLOYMENT.md          # Este arquivo
└── zapi_notes.txt         # Notas sobre Z-API
```
