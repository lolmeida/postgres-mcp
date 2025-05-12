#!/bin/bash
# Script para gerenciar o PostgreSQL MCP usando Docker

# Cores para saída
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções auxiliares
function echo_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

function echo_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

function echo_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

function echo_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Verifica se o Docker está instalado
if ! command -v docker &> /dev/null; then
  echo_error "Docker não está instalado. Por favor, instale o Docker primeiro."
  exit 1
fi

# Verifica se o Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
  echo_warning "Docker Compose não está instalado. Tentando usar 'docker compose' diretamente."
  COMPOSE_CMD="docker compose"
else
  COMPOSE_CMD="docker-compose"
fi

# Função para iniciar os serviços
function start_services() {
  echo_info "Iniciando serviços PostgreSQL e MCP..."
  
  # Verifica se o arquivo docker-compose.yml existe
  if [ ! -f "docker-compose.yml" ]; then
    echo_error "Arquivo docker-compose.yml não encontrado. Certifique-se de que está no diretório correto."
    exit 1
  fi
  
  $COMPOSE_CMD up -d
  
  if [ $? -eq 0 ]; then
    echo_success "Serviços iniciados com sucesso!"
    echo_info "PostgreSQL disponível na porta 5432"
    echo_info "MCP Server disponível na porta 8432"
  else
    echo_error "Falha ao iniciar os serviços. Verifique os logs para mais detalhes."
  fi
}

# Função para parar os serviços
function stop_services() {
  echo_info "Parando serviços..."
  $COMPOSE_CMD down
  
  if [ $? -eq 0 ]; then
    echo_success "Serviços parados com sucesso!"
  else
    echo_error "Falha ao parar os serviços."
  fi
}

# Função para reiniciar os serviços
function restart_services() {
  echo_info "Reiniciando serviços..."
  $COMPOSE_CMD restart
  
  if [ $? -eq 0 ]; then
    echo_success "Serviços reiniciados com sucesso!"
  else
    echo_error "Falha ao reiniciar os serviços."
  fi
}

# Função para exibir logs
function show_logs() {
  echo_info "Exibindo logs dos serviços..."
  $COMPOSE_CMD logs $1
}

# Função para exibir status dos serviços
function show_status() {
  echo_info "Status dos serviços:"
  $COMPOSE_CMD ps
}

# Função para limpar volumes (remove dados)
function clean_data() {
  echo_warning "Esta ação irá remover todos os dados do PostgreSQL."
  read -p "Tem certeza que deseja continuar? (s/N): " confirmation
  
  if [[ $confirmation =~ ^[Ss]$ ]]; then
    echo_info "Removendo serviços e volumes..."
    $COMPOSE_CMD down -v
    
    if [ $? -eq 0 ]; then
      echo_success "Dados removidos com sucesso."
    else
      echo_error "Falha ao remover dados."
    fi
  else
    echo_info "Operação cancelada."
  fi
}

# Menu de ajuda
function show_help() {
  echo -e "${BLUE}PostgreSQL MCP - Utilitário de Gerenciamento${NC}"
  echo ""
  echo "Uso: $0 [comando]"
  echo ""
  echo "Comandos disponíveis:"
  echo "  start       Inicia os serviços PostgreSQL e MCP"
  echo "  stop        Para os serviços"
  echo "  restart     Reinicia os serviços"
  echo "  logs        Exibe logs dos serviços"
  echo "  ps          Exibe status dos serviços"
  echo "  clean       Remove todos os dados (volumes)"
  echo "  help        Exibe esta mensagem de ajuda"
  echo ""
}

# Processar comando
case "$1" in
  start)
    start_services
    ;;
  stop)
    stop_services
    ;;
  restart)
    restart_services
    ;;
  logs)
    show_logs $2
    ;;
  ps)
    show_status
    ;;
  clean)
    clean_data
    ;;
  help|*)
    show_help
    ;;
esac 