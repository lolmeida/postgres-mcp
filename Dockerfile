FROM node:16-alpine

# Diretório de trabalho
WORKDIR /app

# Instalar dependências
COPY package.json ./

# Instalar dependências
RUN npm install

# Copiar código-fonte
COPY . .

# Construir a aplicação
RUN npm run build

# Porta que o servidor MCP irá escutar
EXPOSE 8432

# Comando para iniciar a aplicação
CMD ["node", "dist/index.js"] 