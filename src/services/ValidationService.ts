/**
 * Validation Service Implementation
 * 
 * This service provides data validation utilities using Joi schemas,
 * with standardized error handling and validation processing.
 */

import Joi from 'joi';
import { AbstractService } from './ServiceBase';
import { createComponentLogger } from '../utils/logger';

/**
 * Structure for validation error details
 */
export interface ValidationErrorDetail {
  path: (string | number)[];  // Changed from string[] to support array indexes
  message: string;
  type: string;
  context?: Record<string, any>;
}

/**
 * Result of a validation operation
 */
export interface ValidationResult<T> {
  /**
   * Whether validation was successful
   */
  isValid: boolean;
  
  /**
   * Validated and sanitized data (when valid)
   */
  value?: T;
  
  /**
   * Validation error details (when invalid)
   */
  errors?: ValidationErrorDetail[];
  
  /**
   * Summary error message
   */
  message?: string;
}

/**
 * Options for validation
 */
export interface ValidationOptions {
  /**
   * Whether to abort early on first error
   */
  abortEarly?: boolean;
  
  /**
   * Whether to allow unknown properties
   */
  allowUnknown?: boolean;
  
  /**
   * Whether to strip unknown properties
   */
  stripUnknown?: boolean;
}

/**
 * Service for data validation
 */
export class ValidationService extends AbstractService {
  private logger;
  private customExtensions: Map<string, any> = new Map();
  
  /**
   * Creates a new ValidationService instance
   */
  constructor() {
    super();
    this.logger = createComponentLogger('ValidationService');
    this.registerCustomExtensions();
  }
  
  /**
   * Initialize the service
   */
  async initialize(): Promise<void> {
    this.logger.debug('Initializing ValidationService');
    return Promise.resolve();
  }
  
  /**
   * Validates data against a Joi schema
   * 
   * @param data Data to validate
   * @param schema Joi schema to validate against
   * @param options Validation options
   * @returns Validation result
   */
  validate<T>(
    data: any,
    schema: Joi.Schema,
    options: ValidationOptions = {}
  ): ValidationResult<T> {
    if (!schema) {
      throw this.createError('Validation schema is required', 'validation_error');
    }
    
    const joiOptions: Joi.ValidationOptions = {
      abortEarly: options.abortEarly ?? false,
      allowUnknown: options.allowUnknown ?? true,
      stripUnknown: options.stripUnknown ?? false
    };
    
    try {
      const result = schema.validate(data, joiOptions);
      
      if (result.error) {
        const errors = result.error.details.map(detail => ({
          path: detail.path,
          message: detail.message,
          type: detail.type,
          context: detail.context
        }));
        
        this.logger.debug('Validation failed', { errors });
        
        return {
          isValid: false,
          errors,
          message: result.error.message
        };
      }
      
      return {
        isValid: true,
        value: result.value as T
      };
    } catch (error: any) {
      this.logger.error('Validation error', error);
      
      return {
        isValid: false,
        message: `Validation error: ${error.message}`,
        errors: [{
          path: [],
          message: error.message,
          type: 'internal_error'
        }]
      };
    }
  }
  
  /**
   * Gets a validation schema by name from the defined schemas
   * 
   * @param schemaName Name of the pre-defined schema
   * @returns Joi schema or undefined if not found
   */
  getSchema(schemaName: string): Joi.Schema | undefined {
    try {
      const schemas = require('../models/ValidationSchemas');
      return schemas[`${schemaName}Schema`];
    } catch (error) {
      this.logger.error(`Schema not found: ${schemaName}`, error);
      return undefined;
    }
  }
  
  /**
   * Validates data against a named schema
   * 
   * @param data Data to validate
   * @param schemaName Name of the pre-defined schema
   * @param options Validation options
   * @returns Validation result
   */
  validateWithSchema<T>(
    data: any,
    schemaName: string,
    options: ValidationOptions = {}
  ): ValidationResult<T> {
    const schema = this.getSchema(schemaName);
    
    if (!schema) {
      throw this.createError(`Schema not found: ${schemaName}`, 'validation_error');
    }
    
    return this.validate<T>(data, schema, options);
  }
  
  /**
   * Creates a dynamic schema for a specific entity based on its properties
   * 
   * @param requiredFields Array of field names that should be required
   * @param additionalFieldSchemas Additional schema definitions for specific fields
   * @returns Joi schema
   */
  createEntitySchema(
    requiredFields: string[] = [],
    additionalFieldSchemas: Record<string, Joi.Schema> = {}
  ): Joi.Schema {
    // Default schemas for common field patterns
    const schemaMap: Joi.SchemaMap = {
      // Common field patterns
      id: Joi.alternatives().try(
        Joi.string().trim().max(100),
        Joi.number().integer().positive()
      ),
      email: Joi.string().email().max(255),
      name: Joi.string().trim().max(255),
      description: Joi.string().trim().max(5000),
      status: Joi.string().trim().max(50),
      created_at: Joi.date(),
      updated_at: Joi.date(),
      deleted_at: Joi.date().allow(null)
    };
    
    // Override with additional field schemas
    Object.entries(additionalFieldSchemas).forEach(([field, schema]) => {
      schemaMap[field] = schema;
    });
    
    // Create the schema
    let schema = Joi.object(schemaMap);
    
    // Make fields required if specified
    if (requiredFields.length > 0) {
      schema = schema.fork(requiredFields, (field) => field.required());
    }
    
    return schema;
  }
  
  /**
   * Registers custom Joi extensions
   */
  private registerCustomExtensions(): void {
    // Example of a custom extension: PostgreSQL specific types
    
    // Validation for PostgreSQL interval
    const intervalExtension = {
      type: 'pgInterval',
      base: Joi.string(),
      messages: {
        'pgInterval.format': '{{#label}} must be a valid PostgreSQL interval format'
      },
      validate(value: string, helpers: Joi.CustomHelpers) {
        // Simple regex to validate PostgreSQL interval format
        const intervalRegex = /^(?:\d+\s+(?:year|month|day|hour|minute|second)s?(?:\s+)?)+$/i;
        
        if (!intervalRegex.test(value)) {
          return { value, errors: helpers.error('pgInterval.format') };
        }
        
        return { value };
      }
    };
    
    // Store the extension for future use
    this.customExtensions.set('pgInterval', intervalExtension);
    
    // TODO: Register with Joi when needed
    // To actually register with Joi:
    // const customJoi = Joi.extend(intervalExtension);
  }
} 