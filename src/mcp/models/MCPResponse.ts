/**
 * Modelos de Resposta MCP
 * 
 * Esta implementação contém as interfaces para respostas no formato MCP (Model Context Protocol).
 * Permite estruturar as respostas enviadas pelos handlers para o cliente.
 */

/**
 * Tipo do resultado da resposta
 */
export enum ResponseStatus {
  SUCCESS = 'success',
  ERROR = 'error',
  PARTIAL = 'partial'
}

/**
 * Interface base para todas as respostas MCP
 */
export interface IMCPResponse {
  /**
   * Indica se a operação foi bem-sucedida
   */
  success: boolean;

  /**
   * Tipo de resposta
   */
  status: ResponseStatus;

  /**
   * Dados da resposta (opcional)
   */
  data?: any;

  /**
   * Mensagem adicional (opcional)
   */
  message?: string;
}

/**
 * Interface para respostas MCP com metadados
 */
export interface IMCPResponseWithMetadata extends IMCPResponse {
  /**
   * Identificador único da requisição associada
   */
  requestId?: string;

  /**
   * Timestamp da resposta
   */
  timestamp?: number;

  /**
   * Tempo de processamento em milissegundos
   */
  processingTime?: number;

  /**
   * Metadados adicionais da resposta
   */
  metadata?: Record<string, any>;
}

/**
 * Classe base para respostas MCP
 */
export class MCPResponse implements IMCPResponseWithMetadata {
  success: boolean;
  status: ResponseStatus;
  data?: any;
  message?: string;
  requestId?: string;
  timestamp: number;
  processingTime?: number;
  metadata?: Record<string, any>;

  /**
   * Cria uma nova instância de MCPResponse
   * 
   * @param success Indica se a operação foi bem-sucedida
   * @param status Tipo de resposta
   * @param data Dados da resposta (opcional)
   * @param message Mensagem adicional (opcional)
   * @param requestId Identificador único da requisição associada (opcional)
   * @param processingTime Tempo de processamento em milissegundos (opcional)
   * @param metadata Metadados adicionais da resposta (opcional)
   */
  constructor(
    success: boolean,
    status: ResponseStatus,
    data?: any,
    message?: string,
    requestId?: string,
    processingTime?: number,
    metadata?: Record<string, any>
  ) {
    this.success = success;
    this.status = status;
    this.data = data;
    this.message = message;
    this.requestId = requestId;
    this.timestamp = Date.now();
    this.processingTime = processingTime;
    this.metadata = metadata;
  }

  /**
   * Cria uma resposta de sucesso
   * 
   * @param data Dados da resposta
   * @param message Mensagem adicional (opcional)
   * @param requestId Identificador único da requisição associada (opcional)
   * @param processingTime Tempo de processamento em milissegundos (opcional)
   * @param metadata Metadados adicionais da resposta (opcional)
   * @returns Instância de MCPResponse
   */
  static success(
    data?: any,
    message?: string,
    requestId?: string,
    processingTime?: number,
    metadata?: Record<string, any>
  ): MCPResponse {
    return new MCPResponse(
      true,
      ResponseStatus.SUCCESS,
      data,
      message,
      requestId,
      processingTime,
      metadata
    );
  }

  /**
   * Cria uma resposta de erro
   * 
   * @param message Mensagem de erro
   * @param data Dados adicionais do erro (opcional)
   * @param requestId Identificador único da requisição associada (opcional)
   * @param processingTime Tempo de processamento em milissegundos (opcional)
   * @param metadata Metadados adicionais da resposta (opcional)
   * @returns Instância de MCPResponse
   */
  static error(
    message: string,
    data?: any,
    requestId?: string,
    processingTime?: number,
    metadata?: Record<string, any>
  ): MCPResponse {
    return new MCPResponse(
      false,
      ResponseStatus.ERROR,
      data,
      message,
      requestId,
      processingTime,
      metadata
    );
  }

  /**
   * Cria uma resposta parcial (para streaming)
   * 
   * @param data Dados parciais
   * @param message Mensagem adicional (opcional)
   * @param requestId Identificador único da requisição associada (opcional)
   * @param processingTime Tempo de processamento em milissegundos (opcional)
   * @param metadata Metadados adicionais da resposta (opcional)
   * @returns Instância de MCPResponse
   */
  static partial(
    data?: any,
    message?: string,
    requestId?: string,
    processingTime?: number,
    metadata?: Record<string, any>
  ): MCPResponse {
    return new MCPResponse(
      true,
      ResponseStatus.PARTIAL,
      data,
      message,
      requestId,
      processingTime,
      metadata
    );
  }

  /**
   * Serializa a resposta para JSON
   * 
   * @returns Representação em JSON da resposta
   */
  toJSON(): string {
    return JSON.stringify({
      success: this.success,
      status: this.status,
      data: this.data,
      message: this.message,
      requestId: this.requestId,
      timestamp: this.timestamp,
      processingTime: this.processingTime,
      metadata: this.metadata
    });
  }
} 