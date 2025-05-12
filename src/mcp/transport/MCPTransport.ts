/**
 * Interface de Transporte MCP
 * 
 * Implementação de diferentes modos de transporte para comunicação
 * no protocolo MCP (Model Context Protocol).
 */

import { EventEmitter } from 'events';
import { MCPRequest } from '../models/MCPRequest';
import { MCPResponse } from '../models/MCPResponse';

/**
 * Interface base para todos os transportes MCP
 */
export interface IMCPTransport {
  /**
   * Inicializa o transporte
   */
  initialize(): Promise<void>;

  /**
   * Recebe requisições do cliente
   * 
   * @returns EventEmitter que emite eventos 'request' quando uma requisição é recebida
   */
  receive(): EventEmitter;

  /**
   * Envia uma resposta para o cliente
   * 
   * @param response Resposta a ser enviada
   */
  send(response: MCPResponse): Promise<void>;

  /**
   * Encerra o transporte
   */
  shutdown(): Promise<void>;
}

/**
 * Enum para os modos de transporte disponíveis
 */
export enum TransportMode {
  STDIO = 'stdio',
  HTTP = 'http',
  HTTP_STREAMING = 'http-streaming'
}

/**
 * Classe base para transportes MCP
 */
export abstract class MCPTransportBase implements IMCPTransport {
  protected emitter: EventEmitter;
  
  constructor() {
    this.emitter = new EventEmitter();
  }
  
  abstract initialize(): Promise<void>;
  abstract send(response: MCPResponse): Promise<void>;
  abstract shutdown(): Promise<void>;
  
  /**
   * Recebe requisições do cliente
   * 
   * @returns EventEmitter que emite eventos 'request' quando uma requisição é recebida
   */
  receive(): EventEmitter {
    return this.emitter;
  }

  /**
   * Processa uma string JSON e emite um evento de requisição
   * 
   * @param jsonString String JSON da requisição
   */
  protected processRequest(jsonString: string): void {
    try {
      const data = JSON.parse(jsonString);
      const request = MCPRequest.fromObject(data);
      this.emitter.emit('request', request);
    } catch (error) {
      console.error('Error processing request:', error);
      this.emitter.emit('error', error);
    }
  }
}

/**
 * Implementação de transporte MCP via STDIO
 */
export class MCPStdioTransport extends MCPTransportBase {
  private active: boolean = false;

  /**
   * Inicializa o transporte STDIO
   */
  async initialize(): Promise<void> {
    this.active = true;
    
    // Configura o stdin para receber requisições
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk: string) => {
      if (this.active) {
        this.processRequest(chunk);
      }
    });
    
    process.stdin.on('end', () => {
      this.active = false;
      this.emitter.emit('end');
    });
    
    process.stdin.on('error', (error) => {
      this.emitter.emit('error', error);
    });
    
    // Ignora sinais de término para permitir processamento de requisições
    process.on('SIGINT', () => {
      /* Ignora SIGINT */
    });
    
    process.on('SIGTERM', () => {
      this.shutdown();
    });
  }

  /**
   * Envia uma resposta para o cliente via stdout
   * 
   * @param response Resposta a ser enviada
   */
  async send(response: MCPResponse): Promise<void> {
    if (this.active) {
      process.stdout.write(response.toJSON() + '\n');
    }
  }

  /**
   * Encerra o transporte STDIO
   */
  async shutdown(): Promise<void> {
    this.active = false;
    this.emitter.removeAllListeners();
  }
}

/**
 * Configuração para transporte HTTP
 */
export interface HTTPTransportConfig {
  /**
   * Porta para o servidor HTTP
   */
  port: number;
  
  /**
   * Host para o servidor HTTP
   */
  host?: string;
  
  /**
   * Rota para o endpoint MCP
   */
  path?: string;
  
  /**
   * Timeout para as requisições em milissegundos
   */
  timeout?: number;
  
  /**
   * Cabeçalhos CORS para o servidor HTTP
   */
  corsHeaders?: Record<string, string>;
}

/**
 * Implementação de transporte MCP via HTTP
 * 
 * Observação: Esta é uma implementação vazia, pois a implementação
 * completa depende de bibliotecas externas como Express, que serão
 * adicionadas no momento da implementação.
 */
export class MCPHttpTransport extends MCPTransportBase {
  protected config: HTTPTransportConfig;
  
  constructor(config: HTTPTransportConfig) {
    super();
    this.config = {
      port: config.port,
      host: config.host || 'localhost',
      path: config.path || '/mcp',
      timeout: config.timeout || 30000,
      corsHeaders: config.corsHeaders || {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
      }
    };
  }
  
  /**
   * Inicializa o transporte HTTP
   * 
   * Este método deve ser implementado com um servidor HTTP
   * usando Express ou outra biblioteca semelhante.
   */
  async initialize(): Promise<void> {
    throw new Error('MCPHttpTransport.initialize() not implemented. Use a concrete implementation.');
  }
  
  /**
   * Envia uma resposta para o cliente via HTTP
   * 
   * Este método deve ser implementado com a lógica de resposta HTTP
   * adequada para a biblioteca escolhida.
   */
  async send(response: MCPResponse): Promise<void> {
    throw new Error('MCPHttpTransport.send() not implemented. Use a concrete implementation.');
  }
  
  /**
   * Encerra o transporte HTTP
   * 
   * Este método deve parar o servidor HTTP e liberar recursos.
   */
  async shutdown(): Promise<void> {
    throw new Error('MCPHttpTransport.shutdown() not implemented. Use a concrete implementation.');
  }
}

/**
 * Factory para criar instâncias de transporte MCP
 */
export class MCPTransportFactory {
  /**
   * Cria uma instância de transporte MCP baseada no modo especificado
   * 
   * @param mode Modo de transporte
   * @param config Configuração do transporte (para modos que requerem configuração)
   * @returns Instância de transporte MCP
   * @throws Error se o modo de transporte não for suportado
   */
  static createTransport(mode: TransportMode, config?: any): IMCPTransport {
    switch (mode) {
      case TransportMode.STDIO:
        return new MCPStdioTransport();
      
      case TransportMode.HTTP:
      case TransportMode.HTTP_STREAMING:
        if (!config || !config.port) {
          throw new Error(`Transport mode ${mode} requires configuration with at least a port.`);
        }
        return new MCPHttpTransport(config);
      
      default:
        throw new Error(`Unsupported transport mode: ${mode}`);
    }
  }
} 