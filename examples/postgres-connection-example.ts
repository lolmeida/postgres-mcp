/**
 * PostgreSQL Connection Example
 * 
 * This example demonstrates how to use the PostgreSQL connection and repository classes
 * to connect to a database and perform basic operations.
 */

import {
  PostgresConfigBuilder,
  PostgresConnection,
  PostgresConnectionManager,
  PostgresSchemaManager,
  PostgresQueryBuilder,
  PostgresRepository,
  ConditionOperator,
  OrderDirection
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

  protected mapToRow(entity: User): Record<string, any> {
    const row: Record<string, any> = {
      username: entity.username,
      email: entity.email
    };

    // Only include id if it exists
    if (entity.id) {
      row.id = entity.id;
    }

    // Add timestamps for new entities
    if (!entity.created_at) {
      row.created_at = new Date();
    }
    
    row.updated_at = new Date();

    return row;
  }

  /**
   * Find users by email domain
   */
  async findByEmailDomain(domain: string): Promise<User[]> {
    const queryBuilder = new PostgresQueryBuilder()
      .select(['*'])
      .from(this.tableName)
      .where('email', ConditionOperator.LIKE, `%@${domain}`)
      .orderBy('username', OrderDirection.ASC);
    
    const query = queryBuilder.buildQuery();
    const params = queryBuilder.getParameters();
    
    const result = await this.connection.query(query, params);
    return result.rows.map((row: any) => this.mapToEntity(row));
  }
}

/**
 * Main example function
 */
async function runExample() {
  console.log('PostgreSQL Connection Example');
  console.log('----------------------------');

  try {
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

    // Create connection manager
    const connectionManager = new PostgresConnectionManager();
    
    // Add and connect to database
    await connectionManager.createConnection(config, 'default');
    const connection = await connectionManager.getConnection('default');
    
    console.log('Connected to PostgreSQL');

    // Create schema manager to explore database
    const schemaManager = new PostgresSchemaManager(connection);
    
    // List all schemas
    console.log('\nDatabase Schemas:');
    const schemas = await schemaManager.listSchemas();
    schemas.forEach(schema => {
      console.log(`- ${schema.schemaName} (Owner: ${schema.owner})`);
    });

    // List tables in public schema
    console.log('\nTables in public schema:');
    const tables = await schemaManager.listTables('public');
    tables.forEach(table => {
      console.log(`- ${table.tableName} (${table.tableType}, ~${table.estimatedRowCount} rows)`);
    });

    // Create user repository
    const userRepository = new UserRepository(connection);

    // Create schema and table if they don't exist
    try {
      await connection.query(`
        CREATE TABLE IF NOT EXISTS users (
          id SERIAL PRIMARY KEY,
          username VARCHAR(100) NOT NULL,
          email VARCHAR(255) NOT NULL UNIQUE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      console.log('\nCreated users table (if it didn\'t exist)');
    } catch (error) {
      console.error('Error creating table:', error);
    }

    // Insert a new user
    const timestamp = new Date().getTime();
    const newUser: User = {
      username: `johndoe_${timestamp}`,
      email: `john.doe.${timestamp}@example.com`
    };

    console.log('\nCreating new user:', newUser);
    const createdUser = await userRepository.create(newUser);
    console.log('User created:', createdUser);

    // Find all users
    console.log('\nAll users:');
    const allUsers = await userRepository.findAll();
    allUsers.forEach(user => {
      console.log(`- ${user.username} (${user.email})`);
    });

    // Find user by ID
    if (createdUser.id) {
      console.log(`\nFinding user by ID: ${createdUser.id}`);
      const foundUser = await userRepository.findById(createdUser.id);
      console.log('Found user:', foundUser);
    }

    // Update user
    if (createdUser.id) {
      const userUpdate: Partial<User> = {
        username: 'johndoe_updated',
        email: createdUser.email
      };
      
      console.log(`\nUpdating user ${createdUser.id}:`, userUpdate);
      const updatedUser = await userRepository.update(createdUser.id, userUpdate);
      console.log('Updated user:', updatedUser);
    }

    // Use custom repository method
    console.log('\nFinding users with example.com email:');
    const exampleUsers = await userRepository.findByEmailDomain('example.com');
    exampleUsers.forEach(user => {
      console.log(`- ${user.username} (${user.email})`);
    });

    // Transaction example
    console.log('\nPerforming operations in a transaction:');
    await userRepository.withTransaction(async (transactionalRepo) => {
      // Create a user in the transaction
      const transactionUser: User = {
        username: 'transaction_user',
        email: 'transaction@example.com'
      };
      
      console.log('Creating user in transaction:', transactionUser);
      const createdInTransaction = await transactionalRepo.create(transactionUser);
      console.log('User created in transaction:', createdInTransaction);
      
      // You can throw an error here to test rollback
      // throw new Error('Simulated error to trigger rollback');
      
      return createdInTransaction;
    });

    // Count users
    const userCount = await userRepository.count();
    console.log(`\nTotal users: ${userCount}`);

    // Close connection
    await connectionManager.closeAllConnections();
    console.log('\nConnection closed');

  } catch (error) {
    console.error('Error:', error);
  }
}

// Run the example if this file is executed directly
if (require.main === module) {
  runExample().catch(console.error);
}

export default runExample; 