/**
 * Cache Service Implementation
 * 
 * This service provides caching functionality for database queries and other
 * operations, improving performance by storing frequently accessed data in memory.
 */

import { AbstractService } from './ServiceBase';
import { createComponentLogger } from '../utils/logger';

/**
 * Cache entry with value and metadata
 */
interface CacheEntry<T> {
  /**
   * Cached value
   */
  value: T;
  
  /**
   * When the entry was created
   */
  createdAt: number;
  
  /**
   * When the entry expires (timestamp)
   */
  expiresAt: number;
  
  /**
   * Number of times this entry has been accessed
   */
  hits: number;
  
  /**
   * Last access time
   */
  lastAccessed: number;
  
  /**
   * Tags for the cache entry (for group invalidation)
   */
  tags: string[];
}

/**
 * Cache service statistics
 */
export interface CacheStats {
  /**
   * Total number of items in cache
   */
  size: number;
  
  /**
   * Total number of cache hits
   */
  hits: number;
  
  /**
   * Total number of cache misses
   */
  misses: number;
  
  /**
   * Hit rate (hits / (hits + misses))
   */
  hitRate: number;
  
  /**
   * Number of expired items purged
   */
  expired: number;
  
  /**
   * Memory usage estimate (bytes)
   */
  memoryUsage: number;
}

/**
 * Options for the cache service
 */
export interface CacheOptions {
  /**
   * Default TTL for cache entries in milliseconds
   */
  defaultTtl?: number;
  
  /**
   * Maximum number of items to store in cache
   */
  maxItems?: number;
  
  /**
   * How often to check for expired entries (in milliseconds)
   */
  checkInterval?: number;
  
  /**
   * Whether to automatically start the cleanup interval
   */
  autoStart?: boolean;
}

/**
 * Options for setting a cache entry
 */
export interface SetOptions {
  /**
   * Time-to-live in milliseconds
   */
  ttl?: number;
  
  /**
   * Tags to associate with the entry (for group invalidation)
   */
  tags?: string[];
}

/**
 * Service for caching data to improve performance
 */
export class CacheService extends AbstractService {
  private logger;
  private cache: Map<string, CacheEntry<any>> = new Map();
  private options: Required<CacheOptions>;
  private hits: number = 0;
  private misses: number = 0;
  private expired: number = 0;
  private cleanupInterval: NodeJS.Timeout | null = null;
  
  /**
   * Creates a new CacheService instance
   * 
   * @param options Cache options
   */
  constructor(options: CacheOptions = {}) {
    super();
    this.logger = createComponentLogger('CacheService');
    
    // Set defaults for options
    this.options = {
      defaultTtl: options.defaultTtl || 5 * 60 * 1000, // 5 minutes
      maxItems: options.maxItems || 1000,
      checkInterval: options.checkInterval || 60 * 1000, // 1 minute
      autoStart: options.autoStart !== false
    };
    
    // Start the cleanup interval if enabled
    if (this.options.autoStart) {
      this.startCleanupInterval();
    }
  }
  
  /**
   * Initialize the service
   */
  async initialize(): Promise<void> {
    this.logger.debug('Initializing CacheService', {
      defaultTtl: this.options.defaultTtl,
      maxItems: this.options.maxItems,
      checkInterval: this.options.checkInterval
    });
    
    return Promise.resolve();
  }
  
  /**
   * Get a value from the cache
   * 
   * @param key Cache key
   * @returns Cached value or undefined if not found or expired
   */
  get<T>(key: string): T | undefined {
    // Check if the key exists in the cache
    if (!this.cache.has(key)) {
      this.misses++;
      return undefined;
    }
    
    const entry = this.cache.get(key)!;
    
    // Check if the entry has expired
    if (Date.now() > entry.expiresAt) {
      this.expired++;
      this.cache.delete(key);
      this.misses++;
      return undefined;
    }
    
    // Update hit count and last accessed time
    entry.hits++;
    entry.lastAccessed = Date.now();
    this.hits++;
    
    return entry.value as T;
  }
  
  /**
   * Store a value in the cache
   * 
   * @param key Cache key
   * @param value Value to cache
   * @param options Cache options
   * @returns The cache service instance for chaining
   */
  set<T>(key: string, value: T, options: SetOptions = {}): CacheService {
    // Check if we need to evict entries
    if (this.cache.size >= this.options.maxItems && !this.cache.has(key)) {
      this.evictLeastRecentlyUsed();
    }
    
    const ttl = options.ttl ?? this.options.defaultTtl;
    const tags = options.tags ?? [];
    
    this.cache.set(key, {
      value,
      createdAt: Date.now(),
      expiresAt: Date.now() + ttl,
      hits: 0,
      lastAccessed: Date.now(),
      tags
    });
    
    return this;
  }
  
  /**
   * Store a value in the cache with computed value support
   * 
   * If the key doesn't exist in the cache, the valueFactory function is called
   * to compute the value to store.
   * 
   * @param key Cache key
   * @param valueFactory Function to compute the value if not found
   * @param options Cache options
   * @returns The cached or computed value
   */
  async getOrSet<T>(
    key: string,
    valueFactory: () => T | Promise<T>,
    options: SetOptions = {}
  ): Promise<T> {
    // Try to get from cache first
    const cachedValue = this.get<T>(key);
    
    if (cachedValue !== undefined) {
      return cachedValue;
    }
    
    // Not in cache, compute the value
    const value = await valueFactory();
    
    // Store in cache
    this.set(key, value, options);
    
    return value;
  }
  
  /**
   * Check if a key exists in the cache and is not expired
   * 
   * @param key Cache key
   * @returns Whether the key exists in the cache
   */
  has(key: string): boolean {
    if (!this.cache.has(key)) {
      return false;
    }
    
    const entry = this.cache.get(key)!;
    
    if (Date.now() > entry.expiresAt) {
      this.expired++;
      this.cache.delete(key);
      return false;
    }
    
    return true;
  }
  
  /**
   * Remove a key from the cache
   * 
   * @param key Cache key
   * @returns Whether the key was removed
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }
  
  /**
   * Clear all entries from the cache
   */
  clear(): void {
    this.cache.clear();
    this.logger.debug('Cache cleared');
  }
  
  /**
   * Get the number of entries in the cache
   * 
   * @returns Number of entries
   */
  size(): number {
    return this.cache.size;
  }
  
  /**
   * Get statistics about the cache
   * 
   * @returns Cache statistics
   */
  getStats(): CacheStats {
    const totalOps = this.hits + this.misses;
    return {
      size: this.cache.size,
      hits: this.hits,
      misses: this.misses,
      hitRate: totalOps > 0 ? this.hits / totalOps : 0,
      expired: this.expired,
      memoryUsage: this.estimateMemoryUsage()
    };
  }
  
  /**
   * Reset the cache statistics
   */
  resetStats(): void {
    this.hits = 0;
    this.misses = 0;
    this.expired = 0;
  }
  
  /**
   * Manually run the cleanup process to remove expired entries
   * 
   * @returns Number of entries removed
   */
  cleanup(): number {
    const now = Date.now();
    let removed = 0;
    
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key);
        removed++;
        this.expired++;
      }
    }
    
    if (removed > 0) {
      this.logger.debug(`Removed ${removed} expired cache entries`);
    }
    
    return removed;
  }
  
  /**
   * Invalidate all cache entries with a specific tag
   * 
   * @param tag Tag to invalidate
   * @returns Number of entries invalidated
   */
  invalidateByTag(tag: string): number {
    let invalidated = 0;
    
    for (const [key, entry] of this.cache.entries()) {
      if (entry.tags.includes(tag)) {
        this.cache.delete(key);
        invalidated++;
      }
    }
    
    if (invalidated > 0) {
      this.logger.debug(`Invalidated ${invalidated} cache entries with tag "${tag}"`);
    }
    
    return invalidated;
  }
  
  /**
   * Update the TTL for a cache entry
   * 
   * @param key Cache key
   * @param ttl New TTL in milliseconds
   * @returns Whether the TTL was updated
   */
  updateTtl(key: string, ttl: number): boolean {
    if (!this.cache.has(key)) {
      return false;
    }
    
    const entry = this.cache.get(key)!;
    entry.expiresAt = Date.now() + ttl;
    
    return true;
  }
  
  /**
   * Start the cleanup interval
   */
  startCleanupInterval(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
    
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, this.options.checkInterval);
    
    this.logger.debug(`Cleanup interval started (${this.options.checkInterval}ms)`);
  }
  
  /**
   * Stop the cleanup interval
   */
  stopCleanupInterval(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
      this.logger.debug('Cleanup interval stopped');
    }
  }
  
  /**
   * Cleanup resources when the service is no longer needed
   */
  async shutdown(): Promise<void> {
    this.stopCleanupInterval();
    this.clear();
    this.logger.debug('Cache service shut down');
  }
  
  /**
   * Evict the least recently used cache entry
   */
  private evictLeastRecentlyUsed(): void {
    let oldestKey: string | null = null;
    let oldestTime = Infinity;
    
    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccessed < oldestTime) {
        oldestTime = entry.lastAccessed;
        oldestKey = key;
      }
    }
    
    if (oldestKey) {
      this.cache.delete(oldestKey);
      this.logger.debug(`Evicted least recently used cache entry: ${oldestKey}`);
    }
  }
  
  /**
   * Estimate the memory usage of the cache
   * 
   * This is a rough estimation and not 100% accurate
   * 
   * @returns Estimated memory usage in bytes
   */
  private estimateMemoryUsage(): number {
    let size = 0;
    
    // Approximate size for the Map structure itself
    size += 8 * this.cache.size; // Internal pointers
    
    for (const [key, entry] of this.cache.entries()) {
      // Key size
      size += key.length * 2; // UTF-16 characters
      
      // Metadata size
      size += 8 * 4; // timestamps and counters
      
      // Tags size
      size += 8; // Array pointer
      for (const tag of entry.tags) {
        size += tag.length * 2; // UTF-16 characters
      }
      
      // Value size estimation
      try {
        const valueSize = JSON.stringify(entry.value).length * 2;
        size += valueSize;
      } catch (error) {
        size += 100; // Fallback for non-stringifiable objects
      }
    }
    
    return size;
  }
} 