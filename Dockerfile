FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Instalar o pacote em modo de desenvolvimento
RUN pip install -e .

# Variáveis de ambiente padrão (podem ser sobrescritas no docker-compose.yml)
ENV DB_HOST=postgres \
    DB_PORT=5432 \
    DB_NAME=postgres \
    DB_USER=postgres \
    DB_PASSWORD=postgres \
    MCP_MODE=http \
    MCP_PORT=8432 \
    LOG_LEVEL=INFO

# Comando para iniciar a aplicação
CMD ["python", "-m", "postgres_mcp", \
     "--db-host=${DB_HOST}", \
     "--db-port=${DB_PORT}", \
     "--db-name=${DB_NAME}", \
     "--db-user=${DB_USER}", \
     "--db-password=${DB_PASSWORD}", \
     "--mode=${MCP_MODE}", \
     "--port=${MCP_PORT}", \
     "--log-level=${LOG_LEVEL}"] 