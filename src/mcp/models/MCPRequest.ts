/**
 * Modelos de Requisição MCP
 * 
 * Esta implementação contém as interfaces para requisições no formato MCP (Model Context Protocol).
 * Permite estruturar e validar as requisições recebidas antes do processamento pelos handlers.
 */

/**
 * Interface base para todas as requisições MCP
 */
export interface IMCPRequest {
  /** 
   * Nome da ferramenta a ser invocada
   */
  tool: string;
  
  /**
   * Parâmetros para a ferramenta
   */
  parameters?: Record<string, any>;
}

/**
 * Interface para requisições MCP com metadados
 */
export interface IMCPRequestWithMetadata extends IMCPRequest {
  /**
   * Identificador único da requisição
   */
  requestId?: string;
  
  /**
   * Timestamp da requisição
   */
  timestamp?: number;
  
  /**
   * Informações do cliente (opcional)
   */
  client?: {
    /**
     * Identificador do cliente
     */
    id?: string;
    
    /**
     * Versão do cliente
     */
    version?: string;
    
    /**
     * Informações do ambiente do cliente
     */
    environment?: Record<string, string>;
  };
}

/**
 * Classe base para requisições MCP
 */
export class MCPRequest implements IMCPRequestWithMetadata {
  tool: string;
  parameters?: Record<string, any>;
  requestId?: string;
  timestamp?: number;
  client?: {
    id?: string;
    version?: string;
    environment?: Record<string, string>;
  };

  /**
   * Cria uma nova instância de MCPRequest
   * 
   * @param tool Nome da ferramenta a ser invocada
   * @param parameters Parâmetros para a ferramenta
   * @param requestId Identificador único da requisição (opcional)
   * @param client Informações do cliente (opcional)
   */
  constructor(
    tool: string,
    parameters?: Record<string, any>,
    requestId?: string,
    client?: { id?: string; version?: string; environment?: Record<string, string> }
  ) {
    this.tool = tool;
    this.parameters = parameters || {};
    this.requestId = requestId || this.generateRequestId();
    this.timestamp = Date.now();
    this.client = client;
  }

  /**
   * Gera um ID único para a requisição
   * 
   * @returns ID único gerado
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * Converte um objeto genérico em uma instância de MCPRequest
   * 
   * @param data Objeto a ser convertido
   * @returns Instância de MCPRequest
   * @throws Error se o objeto não contiver os campos necessários
   */
  static fromObject(data: any): MCPRequest {
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid request data: must be an object');
    }

    if (!data.tool || typeof data.tool !== 'string') {
      throw new Error('Invalid request data: missing or invalid tool name');
    }

    return new MCPRequest(
      data.tool,
      data.parameters,
      data.requestId,
      data.client
    );
  }

  /**
   * Serializa a requisição para JSON
   * 
   * @returns Representação em JSON da requisição
   */
  toJSON(): string {
    return JSON.stringify({
      tool: this.tool,
      parameters: this.parameters,
      requestId: this.requestId,
      timestamp: this.timestamp,
      client: this.client
    });
  }
} 