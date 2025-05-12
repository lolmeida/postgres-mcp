/**
 * Security Service Implementation
 * 
 * This service provides authentication, authorization, and access control
 * functionality for database operations. It helps enforce security policies
 * and protect sensitive data.
 */

import Joi from 'joi';
import { AbstractService } from './ServiceBase';
import { createComponentLogger } from '../utils/logger';

/**
 * Permission level for database operations
 */
export enum PermissionLevel {
  /**
   * No access
   */
  NONE = 0,
  
  /**
   * Read-only access
   */
  READ = 1,
  
  /**
   * Read and write access
   */
  WRITE = 2,
  
  /**
   * Read, write, and create/alter schema
   */
  ADMIN = 3,
  
  /**
   * Full access including dangerous operations
   */
  SUPERUSER = 4
}

/**
 * Type of database resource
 */
export enum ResourceType {
  /**
   * Database schema
   */
  SCHEMA = 'schema',
  
  /**
   * Database table
   */
  TABLE = 'table',
  
  /**
   * Database view
   */
  VIEW = 'view',
  
  /**
   * Database function
   */
  FUNCTION = 'function',
  
  /**
   * Database procedure
   */
  PROCEDURE = 'procedure',
  
  /**
   * Generic database connection
   */
  CONNECTION = 'connection',
  
  /**
   * Database system resource
   */
  SYSTEM = 'system'
}

/**
 * Resource access rule
 */
export interface AccessRule {
  /**
   * Type of resource
   */
  resourceType: ResourceType;
  
  /**
   * Resource name (schema.table, function name, etc)
   */
  resourceName: string;
  
  /**
   * Permission level
   */
  permissionLevel: PermissionLevel;
}

/**
 * User role definition
 */
export interface Role {
  /**
   * Role name
   */
  name: string;
  
  /**
   * Role description
   */
  description?: string;
  
  /**
   * Default permission level for resources not explicitly listed
   */
  defaultPermission: PermissionLevel;
  
  /**
   * Resource-specific permissions
   */
  permissions: AccessRule[];
}

/**
 * User object with authentication and authorization information
 */
export interface User {
  /**
   * User ID
   */
  id: string;
  
  /**
   * Username
   */
  username: string;
  
  /**
   * User email
   */
  email?: string;
  
  /**
   * Assigned roles
   */
  roles: string[];
  
  /**
   * Whether the user is active
   */
  active: boolean;
  
  /**
   * Expiration date for the user's access
   */
  expiresAt?: Date;
  
  /**
   * Additional metadata
   */
  metadata?: Record<string, any>;
}

/**
 * Security options
 */
export interface SecurityOptions {
  /**
   * Whether to enable security
   */
  enabled?: boolean;
  
  /**
   * Whether to enforce strict validation
   */
  strictMode?: boolean;
  
  /**
   * Default permission when no rules match
   */
  defaultPermission?: PermissionLevel;
  
  /**
   * Whether to log security events
   */
  logEvents?: boolean;
  
  /**
   * Message for access denied errors
   */
  accessDeniedMessage?: string;
}

/**
 * Operation context for permission checks
 */
export interface OperationContext {
  /**
   * Type of operation (SELECT, INSERT, etc.)
   */
  operation: string;
  
  /**
   * Additional context (source IP, client ID, etc.)
   */
  context?: Record<string, any>;
}

/**
 * Service for security and access control
 */
export class SecurityService extends AbstractService {
  private logger;
  private options: Required<SecurityOptions>;
  private roles: Map<string, Role> = new Map();
  private users: Map<string, User> = new Map();
  private defaultUser: User | null = null;
  
  /**
   * Creates a new SecurityService instance
   * 
   * @param options Security options
   */
  constructor(options: SecurityOptions = {}) {
    super();
    this.logger = createComponentLogger('SecurityService');
    
    // Set defaults for options
    this.options = {
      enabled: options.enabled !== false,
      strictMode: options.strictMode ?? false,
      defaultPermission: options.defaultPermission ?? PermissionLevel.NONE,
      logEvents: options.logEvents !== false,
      accessDeniedMessage: options.accessDeniedMessage || 'Access denied'
    };
  }
  
  /**
   * Initialize the service
   */
  async initialize(): Promise<void> {
    this.logger.debug('Initializing SecurityService', {
      enabled: this.options.enabled,
      strictMode: this.options.strictMode
    });
    
    // Setup default roles
    this.setupDefaultRoles();
    
    return Promise.resolve();
  }
  
  /**
   * Enable or disable security
   * 
   * @param enabled Whether security should be enabled
   */
  setEnabled(enabled: boolean): void {
    this.options.enabled = enabled;
    this.logger.info(`Security ${enabled ? 'enabled' : 'disabled'}`);
  }
  
  /**
   * Register a new role
   * 
   * @param role Role definition
   * @returns Created role
   */
  registerRole(role: Role): Role {
    // Validate role
    this.validateRole(role);
    
    this.roles.set(role.name, role);
    this.logger.debug(`Role registered: ${role.name}`);
    
    return role;
  }
  
  /**
   * Get a role by name
   * 
   * @param roleName Role name
   * @returns Role or undefined if not found
   */
  getRole(roleName: string): Role | undefined {
    return this.roles.get(roleName);
  }
  
  /**
   * Delete a role
   * 
   * @param roleName Role name
   * @returns Whether the role was deleted
   */
  deleteRole(roleName: string): boolean {
    const result = this.roles.delete(roleName);
    
    if (result) {
      this.logger.debug(`Role deleted: ${roleName}`);
    }
    
    return result;
  }
  
  /**
   * List all roles
   * 
   * @returns Array of roles
   */
  listRoles(): Role[] {
    return Array.from(this.roles.values());
  }
  
  /**
   * Register a new user
   * 
   * @param user User definition
   * @returns Created user
   */
  registerUser(user: User): User {
    // Validate user
    this.validateUser(user);
    
    // Check that all roles exist
    for (const roleName of user.roles) {
      if (!this.roles.has(roleName)) {
        throw this.createError(`Invalid role: ${roleName}`, 'validation_error');
      }
    }
    
    this.users.set(user.id, user);
    this.logger.debug(`User registered: ${user.username} (${user.id})`);
    
    return user;
  }
  
  /**
   * Get a user by ID
   * 
   * @param userId User ID
   * @returns User or undefined if not found
   */
  getUser(userId: string): User | undefined {
    return this.users.get(userId);
  }
  
  /**
   * Delete a user
   * 
   * @param userId User ID
   * @returns Whether the user was deleted
   */
  deleteUser(userId: string): boolean {
    const result = this.users.delete(userId);
    
    if (result) {
      this.logger.debug(`User deleted: ${userId}`);
    }
    
    return result;
  }
  
  /**
   * List all users
   * 
   * @returns Array of users
   */
  listUsers(): User[] {
    return Array.from(this.users.values());
  }
  
  /**
   * Set the default user
   * 
   * @param user User to set as default, or null to clear
   */
  setDefaultUser(user: User | null): void {
    this.defaultUser = user;
    this.logger.debug(`Default user ${user ? 'set to: ' + user.username : 'cleared'}`);
  }
  
  /**
   * Check if a user has permission to access a resource
   * 
   * @param userId User ID
   * @param resourceType Resource type
   * @param resourceName Resource name
   * @param requiredPermission Required permission level
   * @param context Operation context
   * @returns Whether access is granted
   */
  hasPermission(
    userId: string | null,
    resourceType: ResourceType,
    resourceName: string,
    requiredPermission: PermissionLevel,
    context: OperationContext = { operation: 'ACCESS' }
  ): boolean {
    // If security is disabled, always grant access
    if (!this.options.enabled) {
      return true;
    }
    
    // Get the user
    let user: User | undefined | null = userId ? this.users.get(userId) : this.defaultUser;
    
    // If no user found and strict mode is enabled, deny access
    if (!user) {
      if (this.options.strictMode) {
        this.logSecurityEvent('ACCESS_DENIED', {
          reason: 'USER_NOT_FOUND',
          userId,
          resourceType,
          resourceName,
          requiredPermission
        });
        return false;
      }
      
      // In non-strict mode, grant access based on default permission
      return requiredPermission <= this.options.defaultPermission;
    }
    
    // Check if user is active and not expired
    if (!user.active || (user.expiresAt && user.expiresAt < new Date())) {
      this.logSecurityEvent('ACCESS_DENIED', {
        reason: 'USER_INACTIVE_OR_EXPIRED',
        userId: user.id,
        resourceType,
        resourceName,
        requiredPermission
      });
      return false;
    }
    
    // Get effective permission level for the user and resource
    const effectivePermission = this.getEffectivePermission(user, resourceType, resourceName);
    
    // Check if permission is sufficient
    const granted = effectivePermission >= requiredPermission;
    
    // Log security event
    if (this.options.logEvents) {
      this.logSecurityEvent(granted ? 'ACCESS_GRANTED' : 'ACCESS_DENIED', {
        userId: user.id,
        resourceType,
        resourceName,
        requiredPermission,
        effectivePermission,
        context
      });
    }
    
    return granted;
  }
  
  /**
   * Enforce permission check and throw error if access is denied
   * 
   * @param userId User ID
   * @param resourceType Resource type
   * @param resourceName Resource name
   * @param requiredPermission Required permission level
   * @param context Operation context
   * @throws Error if access is denied
   */
  enforcePermission(
    userId: string | null,
    resourceType: ResourceType,
    resourceName: string,
    requiredPermission: PermissionLevel,
    context: OperationContext = { operation: 'ACCESS' }
  ): void {
    if (!this.hasPermission(userId, resourceType, resourceName, requiredPermission, context)) {
      throw this.createError(
        this.options.accessDeniedMessage,
        'security_error',
        {
          resourceType,
          resourceName,
          requiredPermission,
          context
        }
      );
    }
  }
  
  /**
   * Get the effective permission level for a user and resource
   * 
   * @param user User
   * @param resourceType Resource type
   * @param resourceName Resource name
   * @returns Effective permission level
   */
  private getEffectivePermission(
    user: User,
    resourceType: ResourceType,
    resourceName: string
  ): PermissionLevel {
    let effectivePermission = PermissionLevel.NONE;
    
    // Check all roles assigned to the user
    for (const roleName of user.roles) {
      const role = this.roles.get(roleName);
      
      if (!role) continue;
      
      // Start with the role's default permission
      let rolePermission = role.defaultPermission;
      
      // Check for more specific permissions
      for (const permission of role.permissions) {
        if (permission.resourceType === resourceType) {
          // Check for exact match
          if (permission.resourceName === resourceName) {
            rolePermission = permission.permissionLevel;
            break;
          }
          
          // Check for wildcard match
          if (permission.resourceName === '*') {
            rolePermission = permission.permissionLevel;
            // Don't break, as a more specific rule might follow
          }
          
          // Check for prefix match with wildcard (e.g., "public.*")
          if (permission.resourceName.endsWith('.*')) {
            const prefix = permission.resourceName.substring(0, permission.resourceName.length - 2);
            if (resourceName.startsWith(prefix)) {
              rolePermission = permission.permissionLevel;
              // Don't break, as a more specific rule might follow
            }
          }
        }
      }
      
      // Take the highest permission level from all roles
      effectivePermission = Math.max(effectivePermission, rolePermission);
    }
    
    return effectivePermission;
  }
  
  /**
   * Validate a role definition
   * 
   * @param role Role to validate
   * @throws Error if the role is invalid
   */
  private validateRole(role: Role): void {
    const schema = Joi.object({
      name: Joi.string().required().min(1).max(100),
      description: Joi.string().max(500),
      defaultPermission: Joi.number().min(0).max(4).required(),
      permissions: Joi.array().items(
        Joi.object({
          resourceType: Joi.string().required(),
          resourceName: Joi.string().required(),
          permissionLevel: Joi.number().min(0).max(4).required()
        })
      ).required()
    });
    
    const { error } = schema.validate(role);
    
    if (error) {
      throw this.createError(
        `Invalid role: ${error.message}`,
        'validation_error'
      );
    }
  }
  
  /**
   * Validate a user definition
   * 
   * @param user User to validate
   * @throws Error if the user is invalid
   */
  private validateUser(user: User): void {
    const schema = Joi.object({
      id: Joi.string().required(),
      username: Joi.string().required().min(1).max(100),
      email: Joi.string().email(),
      roles: Joi.array().items(Joi.string()).required(),
      active: Joi.boolean().required(),
      expiresAt: Joi.date(),
      metadata: Joi.object()
    });
    
    const { error } = schema.validate(user);
    
    if (error) {
      throw this.createError(
        `Invalid user: ${error.message}`,
        'validation_error'
      );
    }
  }
  
  /**
   * Log a security-related event
   * 
   * @param eventType Type of event
   * @param details Event details
   */
  private logSecurityEvent(eventType: string, details: Record<string, any>): void {
    if (this.options.logEvents) {
      this.logger.info(`Security event: ${eventType}`, details);
    }
  }
  
  /**
   * Set up default roles
   */
  private setupDefaultRoles(): void {
    // Read-only role
    this.registerRole({
      name: 'readonly',
      description: 'Read-only access to all resources',
      defaultPermission: PermissionLevel.READ,
      permissions: [
        {
          resourceType: ResourceType.SYSTEM,
          resourceName: '*',
          permissionLevel: PermissionLevel.NONE
        }
      ]
    });
    
    // Power user role
    this.registerRole({
      name: 'poweruser',
      description: 'Read-write access to all resources except system',
      defaultPermission: PermissionLevel.WRITE,
      permissions: [
        {
          resourceType: ResourceType.SYSTEM,
          resourceName: '*',
          permissionLevel: PermissionLevel.NONE
        }
      ]
    });
    
    // Admin role
    this.registerRole({
      name: 'admin',
      description: 'Administrative access to all resources',
      defaultPermission: PermissionLevel.ADMIN,
      permissions: [
        {
          resourceType: ResourceType.SYSTEM,
          resourceName: '*',
          permissionLevel: PermissionLevel.ADMIN
        }
      ]
    });
    
    // Superuser role
    this.registerRole({
      name: 'superuser',
      description: 'Full unrestricted access',
      defaultPermission: PermissionLevel.SUPERUSER,
      permissions: []
    });
  }
} 