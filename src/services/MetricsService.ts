/**
 * Metrics Service Implementation
 * 
 * This service provides performance monitoring capabilities, collecting metrics
 * on query execution time, memory usage, cache performance, and other aspects
 * of the application's performance.
 */

import { EventEmitter } from 'events';
import { AbstractService } from './ServiceBase';
import { createComponentLogger } from '../utils/logger';

/**
 * Time measurement for a single operation
 */
export interface TimingMetric {
  /**
   * Name of the operation
   */
  name: string;
  
  /**
   * Category of the operation
   */
  category: string;
  
  /**
   * Start time (high resolution timestamp)
   */
  startTime: [number, number];
  
  /**
   * End time (high resolution timestamp)
   */
  endTime?: [number, number];
  
  /**
   * Duration in milliseconds
   */
  duration?: number;
  
  /**
   * Additional metadata
   */
  metadata?: Record<string, any>;
  
  /**
   * Whether the operation was successful
   */
  success?: boolean;
}

/**
 * Counter metric for counting occurrences
 */
export interface CounterMetric {
  /**
   * Name of the counter
   */
  name: string;
  
  /**
   * Category of the counter
   */
  category: string;
  
  /**
   * Current count value
   */
  value: number;
  
  /**
   * Additional metadata
   */
  metadata?: Record<string, any>;
}

/**
 * Gauge metric for measuring values that can go up and down
 */
export interface GaugeMetric {
  /**
   * Name of the gauge
   */
  name: string;
  
  /**
   * Category of the gauge
   */
  category: string;
  
  /**
   * Current value
   */
  value: number;
  
  /**
   * Additional metadata
   */
  metadata?: Record<string, any>;
}

/**
 * Options for metrics collection
 */
export interface MetricsOptions {
  /**
   * Whether to enable detailed metrics
   */
  enableDetailedMetrics?: boolean;
  
  /**
   * Maximum number of timing metrics to keep in history
   */
  maxTimingHistory?: number;
  
  /**
   * How often to collect system metrics (memory, cpu) in ms
   */
  systemMetricsInterval?: number;
  
  /**
   * Whether to track the memory usage of the process
   */
  trackMemoryUsage?: boolean;
}

/**
 * Service for collecting and reporting metrics
 */
export class MetricsService extends AbstractService {
  private logger;
  private options: Required<MetricsOptions>;
  private timings: Map<string, TimingMetric[]> = new Map();
  private counters: Map<string, CounterMetric> = new Map();
  private gauges: Map<string, GaugeMetric> = new Map();
  private activeTimings: Map<string, TimingMetric> = new Map();
  private eventEmitter: EventEmitter = new EventEmitter();
  private systemMetricsInterval: NodeJS.Timeout | null = null;
  
  /**
   * Creates a new MetricsService instance
   * 
   * @param options Metrics options
   */
  constructor(options: MetricsOptions = {}) {
    super();
    this.logger = createComponentLogger('MetricsService');
    
    // Set defaults for options
    this.options = {
      enableDetailedMetrics: options.enableDetailedMetrics !== false,
      maxTimingHistory: options.maxTimingHistory || 1000,
      systemMetricsInterval: options.systemMetricsInterval || 60000, // 1 minute
      trackMemoryUsage: options.trackMemoryUsage !== false
    };
  }
  
  /**
   * Initialize the service
   */
  async initialize(): Promise<void> {
    this.logger.debug('Initializing MetricsService', {
      enableDetailedMetrics: this.options.enableDetailedMetrics,
      maxTimingHistory: this.options.maxTimingHistory
    });
    
    // Start collecting system metrics if enabled
    if (this.options.trackMemoryUsage) {
      this.startSystemMetricsCollection();
    }
    
    return Promise.resolve();
  }
  
  /**
   * Start timing an operation
   * 
   * @param name Name of the operation
   * @param category Category of the operation
   * @param metadata Additional metadata
   * @returns Unique ID for the timing
   */
  startTiming(name: string, category: string, metadata: Record<string, any> = {}): string {
    const id = `${category}:${name}:${Date.now()}:${Math.random().toString(36).substring(2, 9)}`;
    
    const metric: TimingMetric = {
      name,
      category,
      startTime: process.hrtime(),
      metadata
    };
    
    this.activeTimings.set(id, metric);
    
    return id;
  }
  
  /**
   * End timing for an operation
   * 
   * @param id Timing ID returned from startTiming
   * @param success Whether the operation was successful
   * @param additionalMetadata Additional metadata to merge
   * @returns Duration in milliseconds
   */
  endTiming(
    id: string,
    success: boolean = true,
    additionalMetadata: Record<string, any> = {}
  ): number {
    const metric = this.activeTimings.get(id);
    
    if (!metric) {
      this.logger.warn(`Timing not found: ${id}`);
      return 0;
    }
    
    // Record end time and calculate duration
    metric.endTime = process.hrtime();
    metric.success = success;
    
    // Calculate duration in milliseconds
    const diff = process.hrtime(metric.startTime);
    const duration = (diff[0] * 1000) + (diff[1] / 1000000);
    metric.duration = duration;
    
    // Merge additional metadata
    metric.metadata = {
      ...metric.metadata,
      ...additionalMetadata
    };
    
    // Store the completed timing in history
    if (!this.timings.has(metric.category)) {
      this.timings.set(metric.category, []);
    }
    
    const categoryTimings = this.timings.get(metric.category)!;
    categoryTimings.push(metric);
    
    // Limit history size
    if (categoryTimings.length > this.options.maxTimingHistory) {
      categoryTimings.shift();
    }
    
    // Clean up active timing
    this.activeTimings.delete(id);
    
    // Emit event
    this.eventEmitter.emit('timing', metric);
    
    return duration;
  }
  
  /**
   * Increment a counter
   * 
   * @param name Counter name
   * @param category Counter category
   * @param amount Amount to increment by (default: 1)
   * @param metadata Additional metadata
   * @returns New counter value
   */
  incrementCounter(
    name: string,
    category: string,
    amount: number = 1,
    metadata: Record<string, any> = {}
  ): number {
    const key = `${category}:${name}`;
    
    if (!this.counters.has(key)) {
      this.counters.set(key, {
        name,
        category,
        value: 0,
        metadata
      });
    }
    
    const counter = this.counters.get(key)!;
    counter.value += amount;
    
    // Update metadata
    counter.metadata = {
      ...counter.metadata,
      ...metadata
    };
    
    // Emit event
    this.eventEmitter.emit('counter', counter);
    
    return counter.value;
  }
  
  /**
   * Set a gauge value
   * 
   * @param name Gauge name
   * @param category Gauge category
   * @param value Gauge value
   * @param metadata Additional metadata
   */
  setGauge(
    name: string,
    category: string,
    value: number,
    metadata: Record<string, any> = {}
  ): void {
    const key = `${category}:${name}`;
    
    this.gauges.set(key, {
      name,
      category,
      value,
      metadata
    });
    
    // Emit event
    this.eventEmitter.emit('gauge', this.gauges.get(key));
  }
  
  /**
   * Get the current value of a counter
   * 
   * @param name Counter name
   * @param category Counter category
   * @returns Counter value or 0 if not found
   */
  getCounter(name: string, category: string): number {
    const key = `${category}:${name}`;
    const counter = this.counters.get(key);
    
    return counter?.value || 0;
  }
  
  /**
   * Get the current value of a gauge
   * 
   * @param name Gauge name
   * @param category Gauge category
   * @returns Gauge value or 0 if not found
   */
  getGauge(name: string, category: string): number {
    const key = `${category}:${name}`;
    const gauge = this.gauges.get(key);
    
    return gauge?.value || 0;
  }
  
  /**
   * Get timing metrics for a category
   * 
   * @param category Category to filter by (optional)
   * @returns Array of timing metrics
   */
  getTimings(category?: string): TimingMetric[] {
    if (category) {
      return this.timings.get(category) || [];
    }
    
    // Return all timings
    return Array.from(this.timings.values()).flat();
  }
  
  /**
   * Get all counters
   * 
   * @param category Category to filter by (optional)
   * @returns Array of counter metrics
   */
  getCounters(category?: string): CounterMetric[] {
    const counters = Array.from(this.counters.values());
    
    if (category) {
      return counters.filter(c => c.category === category);
    }
    
    return counters;
  }
  
  /**
   * Get all gauges
   * 
   * @param category Category to filter by (optional)
   * @returns Array of gauge metrics
   */
  getGauges(category?: string): GaugeMetric[] {
    const gauges = Array.from(this.gauges.values());
    
    if (category) {
      return gauges.filter(g => g.category === category);
    }
    
    return gauges;
  }
  
  /**
   * Calculate timing statistics for a category
   * 
   * @param category Category to get stats for
   * @param name Optional name to filter by
   * @returns Timing statistics
   */
  getTimingStats(category: string, name?: string): {
    count: number;
    totalTime: number;
    avgTime: number;
    minTime: number;
    maxTime: number;
    p95Time: number;
    successRate: number;
  } {
    let timings = this.timings.get(category) || [];
    
    if (name) {
      timings = timings.filter(t => t.name === name);
    }
    
    if (timings.length === 0) {
      return {
        count: 0,
        totalTime: 0,
        avgTime: 0,
        minTime: 0,
        maxTime: 0,
        p95Time: 0,
        successRate: 0
      };
    }
    
    const durations = timings
      .filter(t => t.duration !== undefined)
      .map(t => t.duration as number);
    
    durations.sort((a, b) => a - b);
    
    const successCount = timings.filter(t => t.success === true).length;
    
    return {
      count: timings.length,
      totalTime: durations.reduce((sum, val) => sum + val, 0),
      avgTime: durations.reduce((sum, val) => sum + val, 0) / durations.length,
      minTime: durations[0],
      maxTime: durations[durations.length - 1],
      p95Time: durations[Math.floor(durations.length * 0.95)],
      successRate: (successCount / timings.length) * 100
    };
  }
  
  /**
   * Reset all metrics
   */
  resetMetrics(): void {
    this.timings.clear();
    this.counters.clear();
    this.gauges.clear();
    this.activeTimings.clear();
    
    this.logger.debug('Metrics reset');
  }
  
  /**
   * Subscribe to metrics events
   * 
   * @param eventType Event type ('timing', 'counter', 'gauge', 'all')
   * @param listener Event listener
   */
  subscribe(
    eventType: 'timing' | 'counter' | 'gauge' | 'all',
    listener: (metric: TimingMetric | CounterMetric | GaugeMetric) => void
  ): void {
    if (eventType === 'all') {
      this.eventEmitter.on('timing', listener);
      this.eventEmitter.on('counter', listener);
      this.eventEmitter.on('gauge', listener);
    } else {
      this.eventEmitter.on(eventType, listener);
    }
  }
  
  /**
   * Unsubscribe from metrics events
   * 
   * @param eventType Event type ('timing', 'counter', 'gauge', 'all')
   * @param listener Event listener
   */
  unsubscribe(
    eventType: 'timing' | 'counter' | 'gauge' | 'all',
    listener: (metric: TimingMetric | CounterMetric | GaugeMetric) => void
  ): void {
    if (eventType === 'all') {
      this.eventEmitter.off('timing', listener);
      this.eventEmitter.off('counter', listener);
      this.eventEmitter.off('gauge', listener);
    } else {
      this.eventEmitter.off(eventType, listener);
    }
  }
  
  /**
   * Generate a metrics report with all collected metrics
   * 
   * @returns Metrics report object
   */
  generateReport(): Record<string, any> {
    const timingCategories = Array.from(this.timings.keys());
    const timingStats = timingCategories.reduce((acc, category) => {
      acc[category] = this.getTimingStats(category);
      return acc;
    }, {} as Record<string, any>);
    
    return {
      timestamp: new Date().toISOString(),
      counters: this.getCounters(),
      gauges: this.getGauges(),
      timingStats,
      systemMetrics: {
        memory: this.getMemoryUsage()
      }
    };
  }
  
  /**
   * Start collecting system metrics
   */
  startSystemMetricsCollection(): void {
    if (this.systemMetricsInterval) {
      clearInterval(this.systemMetricsInterval);
    }
    
    // Collect initial metrics
    this.collectSystemMetrics();
    
    // Set up interval for collection
    this.systemMetricsInterval = setInterval(() => {
      this.collectSystemMetrics();
    }, this.options.systemMetricsInterval);
    
    this.logger.debug(`System metrics collection started (${this.options.systemMetricsInterval}ms interval)`);
  }
  
  /**
   * Stop collecting system metrics
   */
  stopSystemMetricsCollection(): void {
    if (this.systemMetricsInterval) {
      clearInterval(this.systemMetricsInterval);
      this.systemMetricsInterval = null;
      this.logger.debug('System metrics collection stopped');
    }
  }
  
  /**
   * Cleanup resources when the service is no longer needed
   */
  async shutdown(): Promise<void> {
    this.stopSystemMetricsCollection();
    this.eventEmitter.removeAllListeners();
    this.logger.debug('Metrics service shut down');
    
    return Promise.resolve();
  }
  
  /**
   * Measure the execution time of a function
   * 
   * @param category Category for the metric
   * @param name Name for the metric
   * @param fn Function to measure
   * @param metadata Additional metadata
   * @returns Result of the function
   */
  async measure<T>(
    category: string,
    name: string,
    fn: () => Promise<T> | T,
    metadata: Record<string, any> = {}
  ): Promise<T> {
    const timingId = this.startTiming(name, category, metadata);
    
    try {
      const result = await fn();
      this.endTiming(timingId, true);
      return result;
    } catch (error) {
      this.endTiming(timingId, false, { error: (error as Error).message });
      throw error;
    }
  }
  
  /**
   * Collect system metrics (memory usage, etc.)
   */
  private collectSystemMetrics(): void {
    // Memory usage
    const memoryUsage = this.getMemoryUsage();
    
    this.setGauge('rss', 'memory', memoryUsage.rss);
    this.setGauge('heapTotal', 'memory', memoryUsage.heapTotal);
    this.setGauge('heapUsed', 'memory', memoryUsage.heapUsed);
    this.setGauge('external', 'memory', memoryUsage.external);
    
    // More system metrics could be added here (CPU usage, etc.)
  }
  
  /**
   * Get memory usage of the current process
   * 
   * @returns Memory usage in bytes
   */
  private getMemoryUsage(): NodeJS.MemoryUsage {
    return process.memoryUsage();
  }
} 