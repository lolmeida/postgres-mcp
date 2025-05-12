/**
 * Módulo de logging para o PostgreSQL MCP
 * 
 * Este módulo fornece uma interface consistente para logging em toda a aplicação,
 * utilizando winston como base e permitindo configuração flexível.
 */

import winston from 'winston';
import { MCPConfig } from '../core/MCPConfig';

/**
 * Cria e configura um logger com base nas configurações fornecidas
 * 
 * @param config Configurações do MCP
 * @returns Instância do logger configurada
 */
export function createLogger(config: Partial<MCPConfig> = {}) {
  // Se uma instância de logger personalizada for fornecida, use-a
  if (config.logger) {
    return config.logger;
  }

  // Determina o nível de log
  const level = config.logLevel || 'info';

  // Formatos de log padrão
  const formats = winston.format.combine(
    winston.format.timestamp({
      format: 'YYYY-MM-DD HH:mm:ss'
    }),
    winston.format.errors({ stack: true }),
    winston.format.splat(),
    winston.format.printf(info => {
      const { timestamp, level, message, ...rest } = info;
      const restString = Object.keys(rest).length ? JSON.stringify(rest, null, 2) : '';
      return `[${timestamp}] [${level.toUpperCase()}]: ${message} ${restString}`;
    })
  );

  // Cria a instância do logger
  return winston.createLogger({
    level,
    format: formats,
    defaultMeta: { service: 'mcp-postgres-js' },
    transports: [
      new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize({ all: true }),
          formats
        )
      }),
      // Suporte para logging em arquivo, desabilitado por padrão
      // new winston.transports.File({ filename: 'error.log', level: 'error' }),
      // new winston.transports.File({ filename: 'combined.log' }),
    ],
  });
}

/**
 * Instância de logger padrão para uso na aplicação
 */
export const defaultLogger = createLogger();

/**
 * Função para criar um logger específico de um componente
 * 
 * @param componentName Nome do componente para adicionar a todos os logs
 * @param config Configurações opcionais
 * @returns Logger específico do componente
 */
export function createComponentLogger(componentName: string, config?: Partial<MCPConfig>) {
  const logger = config ? createLogger(config) : defaultLogger;
  
  return {
    debug: (message: string, meta?: any) => logger.debug(`[${componentName}] ${message}`, meta),
    info: (message: string, meta?: any) => logger.info(`[${componentName}] ${message}`, meta),
    warn: (message: string, meta?: any) => logger.warn(`[${componentName}] ${message}`, meta),
    error: (message: string, meta?: any) => logger.error(`[${componentName}] ${message}`, meta),
  };
} 