#!/bin/bash

# Cores para melhorar a visualização
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para exibir mensagens
print_message() {
  echo -e "${GREEN}[MCP]${NC} $1"
}

# Função para exibir mensagens de erro
print_error() {
  echo -e "${RED}[ERRO]${NC} $1"
}

# Função para exibir mensagens de aviso
print_warning() {
  echo -e "${YELLOW}[AVISO]${NC} $1"
}

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
  print_error "Docker não encontrado. Por favor, instale o Docker e tente novamente."
  exit 1
fi

# Verificar se o Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
  print_error "Docker Compose não encontrado. Por favor, instale o Docker Compose e tente novamente."
  exit 1
fi

case "$1" in
  start)
    print_message "Iniciando os serviços PostgreSQL e MCP..."
    docker-compose up -d
    print_message "Serviços iniciados."
    print_message "PostgreSQL disponível em: localhost:5432"
    print_message "MCP disponível em: localhost:8432"
    ;;
  stop)
    print_message "Parando os serviços..."
    docker-compose down
    print_message "Serviços parados."
    ;;
  restart)
    print_message "Reiniciando os serviços..."
    docker-compose down
    docker-compose up -d
    print_message "Serviços reiniciados."
    ;;
  logs)
    print_message "Exibindo logs..."
    docker-compose logs -f
    ;;
  ps)
    print_message "Status dos serviços:"
    docker-compose ps
    ;;
  build)
    print_message "Construindo as imagens..."
    docker-compose build
    print_message "Imagens construídas."
    ;;
  test)
    print_message "Testando a conexão com o MCP..."
    curl -s -X POST http://localhost:8432 -H "Content-Type: application/json" -d '{"tool": "get_metrics", "parameters": {}}' | jq
    ;;
  setup-cursor)
    print_message "Configurando o Cursor para usar o MCP PostgreSQL..."
    mkdir -p ~/.cursor
    cat > ~/.cursor/mcp.json << EOL
{
    "mcpServers": {
        "postgres": {
            "command": "docker",
            "args": [
                "exec",
                "-it",
                "postgres-mcp-app",
                "python",
                "-m",
                "postgres_mcp",
                "--db-host=postgres",
                "--db-port=5432",
                "--db-name=postgres",
                "--db-user=postgres",
                "--db-password=postgres",
                "--mode=http",
                "--port=8432"
            ],
            "cwd": "/"
        }
    }
}
EOL
    print_message "Configuração do Cursor concluída. Reinicie o Cursor para aplicar as alterações."
    ;;
  *)
    echo "Uso: $0 {start|stop|restart|logs|ps|build|test|setup-cursor}"
    echo ""
    echo "Comandos:"
    echo "  start         Inicia os serviços"
    echo "  stop          Para os serviços"
    echo "  restart       Reinicia os serviços"
    echo "  logs          Exibe os logs dos serviços"
    echo "  ps            Exibe o status dos serviços"
    echo "  build         Constrói as imagens"
    echo "  test          Testa a conexão com o MCP"
    echo "  setup-cursor  Configura o Cursor para usar o MCP PostgreSQL"
    ;;
esac 