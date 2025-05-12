/**
 * Service Layer Example
 * 
 * This example demonstrates how to use the service layer components.
 */

import {
  PostgresConfigBuilder,
  PostgresConnection,
  PostgresConnectionManager,
  PostgresRepository,
  TableService,
  QueryService,
  SchemaService,
  TransactionService,
  ValidationService,
  IsolationLevel
} from '../src';

/**
 * Basic user entity
 */
interface User {
  id?: number;
  username: string;
  email: string;
  created_at?: Date;
  updated_at?: Date;
}

/**
 * User repository implementation
 */
class UserRepository extends PostgresRepository<User> {
  constructor(connection: PostgresConnection) {
    super(connection, 'users');
  }

  protected mapToEntity(row: Record<string, any>): User {
    return {
      id: row.id,
      username: row.username,
      email: row.email,
      created_at: row.created_at,
      updated_at: row.updated_at
    };
  }
}

/**
 * Example showing how to use the service layer
 */
async function runExample() {
  try {
    console.log('=== PostgreSQL MCP Service Layer Example ===');
    
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
    
    // Setup test table if it doesn't exist
    await setupTestTable(connection);

    // Create services
    const tableService = new TableService(connection);
    const queryService = new QueryService(connection);
    const schemaService = new SchemaService(connection);
    const transactionService = new TransactionService(connection);
    const validationService = new ValidationService();
    
    // Initialize services
    await tableService.initialize();
    await queryService.initialize();
    await schemaService.initialize();
    await transactionService.initialize();
    await validationService.initialize();
    
    // Example 1: Using SchemaService to explore database structure
    console.log('\n=== Example 1: Exploring Database Structure ===');
    const schemas = await schemaService.listSchemas({ includeSystem: false });
    console.log(`\nAvailable schemas (${schemas.length}):`);
    schemas.forEach(schema => {
      console.log(`- ${schema.schemaName} (owner: ${schema.owner})`);
    });
    
    const tables = await schemaService.listTables('public');
    console.log(`\nTables in 'public' schema (${tables.length}):`);
    tables.forEach(table => {
      console.log(`- ${table.name} (${table.isView ? 'VIEW' : 'TABLE'})`);
    });
    
    if (tables.some(t => t.name === 'users')) {
      const tableDetails = await schemaService.getTableDetails('users');
      console.log('\nDetails for table "users":');
      console.log(`Columns (${tableDetails.columns.length}):`);
      tableDetails.columns.forEach(column => {
        console.log(`- ${column.name}: ${column.type} ${column.isNullable ? 'NULL' : 'NOT NULL'}${column.isPrimaryKey ? ' PRIMARY KEY' : ''}`);
      });
    }
    
    // Example 2: Using QueryService to execute custom SQL
    console.log('\n=== Example 2: Executing Custom SQL ===');
    const queryResult = await queryService.executeQuery(
      'SELECT current_database() as db, current_user as user, version() as version'
    );
    
    console.log('\nDatabase information:');
    if (queryResult.rows.length > 0) {
      const row = queryResult.rows[0];
      console.log(`- Database: ${row.db}`);
      console.log(`- User: ${row.user}`);
      console.log(`- Version: ${row.version}`);
    }
    
    console.log(`\nQuery executed in ${queryResult.executionTime} ms`);
    
    // Example 3: Using TableService to perform CRUD operations
    console.log('\n=== Example 3: Table Operations ===');
    
    // Create a custom repository factory for the TableService
    const createUserRepository = (connection: PostgresConnection, tableName: string, schemaName: string) => {
      return new UserRepository(connection);
    };
    
    // Create a new user
    const timestamp = new Date().getTime();
    const newUser: User = {
      username: `johndoe_${timestamp}`,
      email: `john.doe.${timestamp}@example.com`
    };
    
    console.log('\nCreating new user:', newUser);
    const createdUser = await tableService.createRecord<User>(
      'users',
      'public',
      newUser,
      createUserRepository
    );
    
    console.log('User created:', createdUser);
    
    // Read users from table
    console.log('\nReading users table:');
    const usersResult = await tableService.readTable<User>(
      'users',
      'public',
      { limit: 5 },
      createUserRepository
    );
    
    console.log(`Found ${usersResult.count} users (showing ${usersResult.records.length}):`);
    usersResult.records.forEach(user => {
      console.log(`- ID: ${user.id}, Username: ${user.username}, Email: ${user.email}`);
    });
    
    // Update user with TableService
    if (createdUser.id) {
      const userUpdate = {
        username: `${createdUser.username}_updated`,
        email: createdUser.email
      };
      
      console.log(`\nUpdating user ${createdUser.id}:`, userUpdate);
      const updatedUser = await tableService.updateRecord<User>(
        'users',
        'public',
        createdUser.id,
        userUpdate,
        createUserRepository
      );
      
      console.log('User updated:', updatedUser);
    }
    
    // Example 4: Using ValidationService
    console.log('\n=== Example 4: Data Validation ===');
    
    // Create a schema for user entity
    const userSchema = validationService.createEntitySchema(
      'user',
      ['username', 'email'],
      {
        username: Joi.string().min(3).max(50).alphanum(),
        email: Joi.string().email()
      }
    );
    
    // Validate valid data
    const validUser = {
      username: 'jsmith',
      email: 'john.smith@example.com'
    };
    
    const validResult = validationService.validate(validUser, userSchema);
    console.log('\nValidating valid user:', validUser);
    console.log('Validation result:', validResult.isValid ? 'VALID' : 'INVALID');
    
    // Validate invalid data
    const invalidUser = {
      username: 'js', // Too short
      email: 'not-an-email'
    };
    
    const invalidResult = validationService.validate(invalidUser, userSchema);
    console.log('\nValidating invalid user:', invalidUser);
    console.log('Validation result:', invalidResult.isValid ? 'VALID' : 'INVALID');
    
    if (!invalidResult.isValid && invalidResult.errors) {
      console.log('Validation errors:');
      invalidResult.errors.forEach(error => {
        console.log(`- ${error.path.join('.')}: ${error.message}`);
      });
    }
    
    // Example 5: Using TransactionService
    console.log('\n=== Example 5: Transaction Management ===');
    
    // Execute operations in a transaction
    const transactionResult = await transactionService.executeInTransaction(async (client) => {
      console.log('\nExecuting operations in transaction...');
      
      // Create a temporary user that will be rolled back
      const tempUser = {
        username: `tempuser_${new Date().getTime()}`,
        email: `temp_${new Date().getTime()}@example.com`
      };
      
      // Execute a query within the transaction
      const result = await client.query(
        'INSERT INTO users(username, email) VALUES($1, $2) RETURNING *',
        [tempUser.username, tempUser.email]
      );
      
      console.log('Created temporary user (will be rolled back):', result.rows[0]);
      
      // Return some data from the transaction
      return { 
        tempUserId: result.rows[0].id,
        success: true
      };
    }, IsolationLevel.READ_COMMITTED);
    
    console.log('Transaction completed:', transactionResult);
    
    // Example of manual transaction management with savepoints
    console.log('\nManual transaction management with savepoints:');
    
    const tx = await transactionService.beginTransaction();
    console.log(`Transaction started: ${tx.id}`);
    
    try {
      const client = transactionService.getTransactionClient(tx.id);
      
      // Create a user that will be committed
      const permanentUser = {
        username: `permanent_${new Date().getTime()}`,
        email: `permanent_${new Date().getTime()}@example.com`
      };
      
      await client.query(
        'INSERT INTO users(username, email) VALUES($1, $2)',
        [permanentUser.username, permanentUser.email]
      );
      
      console.log('Created permanent user (will be committed):', permanentUser);
      
      // Create a savepoint
      await transactionService.createSavepoint(tx.id, 'before_temp_user');
      
      // Create a temporary user that will be rolled back to savepoint
      const anotherTempUser = {
        username: `another_temp_${new Date().getTime()}`,
        email: `another_temp_${new Date().getTime()}@example.com`
      };
      
      await client.query(
        'INSERT INTO users(username, email) VALUES($1, $2)',
        [anotherTempUser.username, anotherTempUser.email]
      );
      
      console.log('Created another temporary user (will be rolled back to savepoint):', anotherTempUser);
      
      // Roll back to savepoint
      await transactionService.rollbackTransaction(tx.id, 'before_temp_user');
      console.log('Rolled back to savepoint "before_temp_user"');
      
      // Commit the transaction
      await transactionService.commitTransaction(tx.id);
      console.log('Transaction committed');
    } catch (error) {
      console.error('Transaction error:', error);
      await transactionService.rollbackTransaction(tx.id);
      console.log('Transaction rolled back due to error');
    }
    
    // Cleanup connection
    await connectionManager.removeConnection('default');
    console.log('\nExample completed successfully!');
    
  } catch (error) {
    console.error('Error in example:', error);
  }
}

/**
 * Helper function to set up the test table
 */
async function setupTestTable(connection: PostgresConnection): Promise<void> {
  try {
    // Check if users table exists
    const result = await connection.query(`
      SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'users'
      );
    `);
    
    const tableExists = result.rows[0].exists;
    
    if (!tableExists) {
      console.log('Creating users table...');
      
      await connection.query(`
        CREATE TABLE users (
          id SERIAL PRIMARY KEY,
          username VARCHAR(50) NOT NULL,
          email VARCHAR(100) NOT NULL UNIQUE,
          created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      console.log('Users table created successfully');
    } else {
      console.log('Users table already exists');
    }
  } catch (error) {
    console.error('Error setting up test table:', error);
    throw error;
  }
}

// Run the example
runExample().catch(console.error);

// For Joi import
import * as Joi from 'joi'; 