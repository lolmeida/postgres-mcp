/**
 * Auxiliary Services Example
 * 
 * This example demonstrates how to use the auxiliary services:
 * - LoggingService: Advanced logging with custom formats, rotation, etc.
 * - CacheService: In-memory caching for expensive operations
 * - MetricsService: Performance metrics collection and reporting
 * - SecurityService: Authentication and authorization
 */

import {
  PostgresConfigBuilder,
  PostgresConnection,
  PostgresConnectionManager,
  LoggingService,
  CacheService,
  MetricsService,
  SecurityService,
  SchemaService,
  ResourceType,
  PermissionLevel,
  QueryService
} from '../src';

/**
 * Example showing how to use the auxiliary services
 */
async function runExample() {
  try {
    console.log('=== PostgreSQL MCP Auxiliary Services Example ===');
    
    // Create PostgreSQL configuration
    const config = new PostgresConfigBuilder()
      .withHost('localhost')
      .withPort(5432)
      .withDatabase('postgres')
      .withUser('postgres')
      .withPassword('postgres')
      .withPool(1, 10)
      .withSSL('disable')
      .build();
    
    // Create connection and connection manager
    const connectionManager = new PostgresConnectionManager();
    await connectionManager.addConnection('default', config);
    const connection = connectionManager.getConnection('default');
    
    // Initialize services we'll use in examples
    const schemaService = new SchemaService(connection);
    const queryService = new QueryService(connection);
    
    // Example 1: Using LoggingService
    console.log('\n=== Example 1: LoggingService ===');
    
    // Create logging service with custom configuration
    const loggingService = new LoggingService({}, {
      logDir: './logs',
      level: 'debug',
      enableConsole: true,
      enableFileLogging: true,
      rotation: {
        maxSize: '10m',
        maxFiles: 5
      }
    });
    
    await loggingService.initialize();
    
    // Get a component logger
    const dbLogger = loggingService.getComponentLogger('Database');
    
    // Log different levels
    dbLogger.info('Database connection established');
    dbLogger.debug('Executing query: SELECT * FROM users');
    dbLogger.warn('Slow query detected (200ms): SELECT * FROM large_table');
    
    try {
      throw new Error('Test error for logging');
    } catch (error) {
      dbLogger.error('Error executing query', error);
    }
    
    console.log('Logging sample entries complete. Check logs directory if file logging is enabled.');
    
    // Example 2: Using CacheService
    console.log('\n=== Example 2: CacheService ===');
    
    // Create cache service with custom configuration
    const cacheService = new CacheService({
      defaultTtl: 30 * 1000, // 30 seconds
      maxItems: 100,
      checkInterval: 10 * 1000, // 10 seconds
      autoStart: true
    });
    
    await cacheService.initialize();
    
    // Store something in cache
    cacheService.set('greeting', 'Hello, world!');
    cacheService.set('complex-data', { id: 1, name: 'Test', items: [1, 2, 3] }, { ttl: 60 * 1000 });
    
    // Retrieve from cache
    const greeting = cacheService.get<string>('greeting');
    console.log('Retrieved from cache:', greeting);
    
    // Get or compute value (useful pattern)
    const data = await cacheService.getOrSet(
      'db-schemas',
      async () => {
        console.log('Cache miss! Fetching schemas from database...');
        const schemas = await schemaService.listSchemas({ includeSystem: false });
        return schemas;
      },
      { ttl: 60 * 1000 }
    );
    
    console.log(`Retrieved ${data.length} schemas (either from cache or computed)`);
    
    // Fetch the same data again - should be from cache now
    const cachedData = await cacheService.getOrSet(
      'db-schemas',
      async () => {
        console.log('Cache miss! Fetching schemas from database...');
        const schemas = await schemaService.listSchemas({ includeSystem: false });
        return schemas;
      }
    );
    
    console.log(`Retrieved ${cachedData.length} schemas on second attempt (should be from cache)`);
    
    // Get some cache statistics
    const stats = cacheService.getStats();
    console.log('Cache statistics:', {
      size: stats.size,
      hits: stats.hits,
      misses: stats.misses,
      hitRate: `${(stats.hitRate * 100).toFixed(1)}%`
    });
    
    // Example 3: Using MetricsService
    console.log('\n=== Example 3: MetricsService ===');
    
    // Create metrics service
    const metricsService = new MetricsService({
      enableDetailedMetrics: true,
      trackMemoryUsage: true
    });
    
    await metricsService.initialize();
    
    // Subscribe to metric events
    metricsService.subscribe('timing', (metric) => {
      console.log(`Timing metric: ${metric.category}.${metric.name} - ${metric.duration}ms`);
    });
    
    // Measure operation execution time
    const queryResult = await metricsService.measure(
      'database',
      'list-tables',
      async () => {
        // Expensive operation to measure
        return await schemaService.listTables('public');
      },
      { connection: 'default' }
    );
    
    console.log(`Measured operation returned ${queryResult.length} tables`);
    
    // Record some basic metrics
    metricsService.incrementCounter('query-executions', 'database');
    metricsService.incrementCounter('rows-read', 'database', queryResult.length);
    metricsService.setGauge('active-connections', 'database', 1);
    
    // Perform a more complex timed operation
    const timingId = metricsService.startTiming('custom-query', 'database');
    
    try {
      // Execute a potentially expensive query
      const result = await queryService.executeQuery('SELECT count(*) FROM pg_catalog.pg_tables');
      metricsService.endTiming(timingId, true, { rows: result.rows.length });
      
      console.log(`Database has ${result.rows[0].count} tables in total`);
    } catch (error) {
      metricsService.endTiming(timingId, false, { error });
      throw error;
    }
    
    // Get timing statistics
    const dbStats = metricsService.getTimingStats('database');
    console.log('Database operation statistics:', {
      count: dbStats.count,
      avgTime: `${dbStats.avgTime.toFixed(2)}ms`,
      maxTime: `${dbStats.maxTime.toFixed(2)}ms`,
      successRate: `${dbStats.successRate.toFixed(1)}%`
    });
    
    // Generate a metrics report
    const report = metricsService.generateReport();
    console.log('Metrics report generated with data from all categories');
    
    // Example 4: Using SecurityService
    console.log('\n=== Example 4: SecurityService ===');
    
    // Create security service
    const securityService = new SecurityService({
      enabled: true,
      strictMode: false,
      logEvents: true
    });
    
    await securityService.initialize();
    
    // Create a custom role
    const developerRole = {
      name: 'developer',
      description: 'Application developer with limited access',
      defaultPermission: PermissionLevel.READ,
      permissions: [
        {
          resourceType: ResourceType.TABLE,
          resourceName: 'public.users',
          permissionLevel: PermissionLevel.WRITE
        },
        {
          resourceType: ResourceType.SCHEMA,
          resourceName: 'public',
          permissionLevel: PermissionLevel.READ
        }
      ]
    };
    
    securityService.registerRole(developerRole);
    
    // Register a user
    const user = {
      id: 'user1',
      username: 'appuser',
      email: 'app.user@example.com',
      roles: ['developer'],
      active: true
    };
    
    securityService.registerUser(user);
    
    // Check permissions for various operations
    const canReadUsers = securityService.hasPermission(
      user.id,
      ResourceType.TABLE,
      'public.users',
      PermissionLevel.READ,
      { operation: 'SELECT' }
    );
    
    const canWriteUsers = securityService.hasPermission(
      user.id,
      ResourceType.TABLE,
      'public.users',
      PermissionLevel.WRITE,
      { operation: 'UPDATE' }
    );
    
    const canDropUsers = securityService.hasPermission(
      user.id,
      ResourceType.TABLE,
      'public.users',
      PermissionLevel.ADMIN,
      { operation: 'DROP' }
    );
    
    console.log('Permission checks for user:', {
      canReadUsers,
      canWriteUsers,
      canDropUsers
    });
    
    // Try to enforce a permission that will fail
    console.log('Attempting to drop a table (should be denied)...');
    try {
      securityService.enforcePermission(
        user.id,
        ResourceType.TABLE,
        'public.users',
        PermissionLevel.ADMIN,
        { operation: 'DROP' }
      );
      console.log('Permission granted (unexpected)');
    } catch (error) {
      console.log('Permission denied (expected):', error.message);
    }
    
    // List all available roles
    const roles = securityService.listRoles();
    console.log(`Available roles (${roles.length}):`, roles.map(r => r.name).join(', '));
    
    // Cleanup
    await connectionManager.removeConnection('default');
    await cacheService.shutdown();
    await metricsService.shutdown();
    
    console.log('\nExample completed successfully!');
    
  } catch (error) {
    console.error('Error in example:', error);
  }
}

// Run the example
runExample().catch(console.error); 