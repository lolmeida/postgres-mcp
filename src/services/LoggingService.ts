/**
 * Logging Service Implementation
 * 
 * This service provides advanced logging capabilities with customizable transports,
 * log rotation, and formatted output. It builds upon the base logger implementation
 * and adds additional functionality for enterprise-grade logging needs.
 */

import fs from 'fs';
import path from 'path';
import winston from 'winston';
import 'winston-daily-rotate-file';
import { AbstractService } from './ServiceBase';
import { MCPConfig } from '../core/MCPConfig';
import { createLogger, createComponentLogger } from '../utils/logger';

/**
 * Log level type
 */
export type LogLevel = 'error' | 'warn' | 'info' | 'http' | 'verbose' | 'debug' | 'silly';

/**
 * Configuration for log file rotation
 */
export interface LogRotationConfig {
  /**
   * Maximum file size before rotation
   */
  maxSize: string;
  
  /**
   * Maximum number of files to keep
   */
  maxFiles: number;
  
  /**
   * Date pattern for file names
   */
  datePattern?: string;
  
  /**
   * Whether to compress rotated logs
   */
  compress?: boolean;
}

/**
 * Configuration for logging service
 */
export interface LoggingServiceConfig {
  /**
   * Base log directory
   */
  logDir?: string;
  
  /**
   * Log level
   */
  level?: LogLevel;
  
  /**
   * Whether to enable console logging
   */
  enableConsole?: boolean;
  
  /**
   * Whether to enable file logging
   */
  enableFileLogging?: boolean;
  
  /**
   * Configuration for log rotation
   */
  rotation?: LogRotationConfig;
  
  /**
   * Additional metadata to include in logs
   */
  defaultMeta?: Record<string, any>;
  
  /**
   * Format for console logs
   */
  consoleFormat?: winston.Logform.Format;
  
  /**
   * Format for file logs
   */
  fileFormat?: winston.Logform.Format;
}

/**
 * Service for advanced logging capabilities
 */
export class LoggingService extends AbstractService {
  private logger: winston.Logger;
  private config: LoggingServiceConfig;
  private transports: winston.transport[] = [];
  private rotatingFileTransports: Map<string, winston.transport> = new Map();
  private componentLoggers: Map<string, any> = new Map();
  
  /**
   * Creates a new LoggingService instance
   * 
   * @param mcpConfig MCP configuration
   * @param serviceConfig Logging service configuration
   */
  constructor(
    private mcpConfig: Partial<MCPConfig> = {},
    serviceConfig: LoggingServiceConfig = {}
  ) {
    super();
    
    // Set defaults for config
    this.config = {
      logDir: serviceConfig.logDir || 'logs',
      level: serviceConfig.level || (mcpConfig.logLevel as LogLevel) || 'info',
      enableConsole: serviceConfig.enableConsole !== false,
      enableFileLogging: serviceConfig.enableFileLogging || false,
      rotation: serviceConfig.rotation || {
        maxSize: '10m',
        maxFiles: 5,
        datePattern: 'YYYY-MM-DD',
        compress: true
      },
      defaultMeta: {
        service: 'mcp-postgres-js',
        ...(serviceConfig.defaultMeta || {})
      }
    };
    
    // Create base logger
    this.initializeLogger();
  }
  
  /**
   * Initialize the service
   */
  async initialize(): Promise<void> {
    this.logger.info('Logging service initialized', {
      level: this.config.level,
      enableConsole: this.config.enableConsole,
      enableFileLogging: this.config.enableFileLogging
    });
    
    return Promise.resolve();
  }
  
  /**
   * Get the underlying winston logger
   * 
   * @returns Winston logger instance
   */
  getLogger(): winston.Logger {
    return this.logger;
  }
  
  /**
   * Create a component-specific logger
   * 
   * @param componentName Name of the component
   * @returns Component logger
   */
  getComponentLogger(componentName: string) {
    if (!this.componentLoggers.has(componentName)) {
      const componentLogger = {
        debug: (message: string, meta?: any) => this.logger.debug(`[${componentName}] ${message}`, meta),
        info: (message: string, meta?: any) => this.logger.info(`[${componentName}] ${message}`, meta),
        warn: (message: string, meta?: any) => this.logger.warn(`[${componentName}] ${message}`, meta),
        error: (message: string, meta?: any) => this.logger.error(`[${componentName}] ${message}`, meta),
        verbose: (message: string, meta?: any) => this.logger.verbose(`[${componentName}] ${message}`, meta),
        http: (message: string, meta?: any) => this.logger.http(`[${componentName}] ${message}`, meta),
        silly: (message: string, meta?: any) => this.logger.silly(`[${componentName}] ${message}`, meta)
      };
      
      this.componentLoggers.set(componentName, componentLogger);
    }
    
    return this.componentLoggers.get(componentName);
  }
  
  /**
   * Add a file transport with optional rotation
   * 
   * @param filename Log file name
   * @param level Log level for this file
   * @param rotation Rotation options
   * @returns The logging service instance for chaining
   */
  addFileTransport(
    filename: string,
    level: LogLevel = 'info',
    rotation: LogRotationConfig = this.config.rotation!
  ): LoggingService {
    // Ensure directory exists
    const logDir = this.config.logDir!;
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    
    const filePath = path.join(logDir, filename);
    
    // Create rotating file transport
    const transport = new (winston.transports as any).DailyRotateFile({
      filename: `${filePath}-%DATE%.log`,
      datePattern: rotation.datePattern,
      zippedArchive: rotation.compress,
      maxSize: rotation.maxSize,
      maxFiles: rotation.maxFiles,
      level
    });
    
    // Store for later reference
    this.rotatingFileTransports.set(filename, transport);
    
    // Add to logger
    this.logger.add(transport);
    
    return this;
  }
  
  /**
   * Remove a file transport
   * 
   * @param filename Log file name
   * @returns The logging service instance for chaining
   */
  removeFileTransport(filename: string): LoggingService {
    if (this.rotatingFileTransports.has(filename)) {
      const transport = this.rotatingFileTransports.get(filename)!;
      this.logger.remove(transport);
      this.rotatingFileTransports.delete(filename);
    }
    
    return this;
  }
  
  /**
   * Set the global log level
   * 
   * @param level New log level
   * @returns The logging service instance for chaining
   */
  setLogLevel(level: LogLevel): LoggingService {
    this.logger.level = level;
    this.config.level = level;
    return this;
  }
  
  /**
   * Add custom metadata to all subsequent logs
   * 
   * @param meta Metadata object
   * @returns The logging service instance for chaining
   */
  addDefaultMetadata(meta: Record<string, any>): LoggingService {
    this.config.defaultMeta = {
      ...this.config.defaultMeta,
      ...meta
    };
    
    // Update logger default meta
    this.logger.defaultMeta = this.config.defaultMeta;
    
    return this;
  }
  
  /**
   * Creates a child logger with additional metadata
   * 
   * @param meta Additional metadata
   * @returns Child logger
   */
  child(meta: Record<string, any>): winston.Logger {
    return this.logger.child(meta);
  }
  
  /**
   * Method to explicitly log an error object with stack trace
   * 
   * @param message Log message
   * @param error Error object
   * @param meta Additional metadata
   */
  logError(message: string, error: Error, meta: Record<string, any> = {}): void {
    this.logger.error(message, {
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack
      },
      ...meta
    });
  }
  
  /**
   * Initialize the winston logger
   */
  private initializeLogger(): void {
    // Create formats
    const baseFormat = winston.format.combine(
      winston.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss.SSS'
      }),
      winston.format.errors({ stack: true }),
      winston.format.splat()
    );
    
    const consoleFormat = this.config.consoleFormat || winston.format.combine(
      baseFormat,
      winston.format.colorize({ all: true }),
      winston.format.printf(info => {
        const { timestamp, level, message, ...rest } = info;
        const metaStr = Object.keys(rest).length > 0 && rest.stack === undefined 
          ? `\n${JSON.stringify(rest, null, 2)}` 
          : '';
        
        return `[${timestamp}] [${level}]: ${message}${metaStr}`;
      })
    );
    
    const fileFormat = this.config.fileFormat || winston.format.combine(
      baseFormat,
      winston.format.json()
    );
    
    // Create transports
    this.transports = [];
    
    if (this.config.enableConsole) {
      this.transports.push(new winston.transports.Console({
        level: this.config.level,
        format: consoleFormat
      }));
    }
    
    // Initialize the logger
    this.logger = winston.createLogger({
      level: this.config.level,
      defaultMeta: this.config.defaultMeta,
      transports: this.transports
    });
    
    // Add file transports if enabled
    if (this.config.enableFileLogging) {
      // Add combined log
      this.addFileTransport('combined.log', this.config.level);
      
      // Add error log
      this.addFileTransport('error.log', 'error');
    }
  }
} 