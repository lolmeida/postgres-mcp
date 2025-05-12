/**
 * PostgreSQL Query Builder
 * 
 * This class provides a fluent interface for building SQL queries for PostgreSQL.
 * It supports SELECT, INSERT, UPDATE, and DELETE operations with conditions,
 * joins, ordering, and pagination.
 */

import { createComponentLogger } from '../utils/logger';
import { DatabaseException, QueryException } from '../utils/exceptions';

/**
 * Join type for SQL joins
 */
export enum JoinType {
  INNER = 'INNER JOIN',
  LEFT = 'LEFT JOIN',
  RIGHT = 'RIGHT JOIN',
  FULL = 'FULL JOIN',
  CROSS = 'CROSS JOIN'
}

/**
 * Order direction for SQL ordering
 */
export enum OrderDirection {
  ASC = 'ASC',
  DESC = 'DESC'
}

/**
 * Condition operator for WHERE clauses
 */
export enum ConditionOperator {
  EQUALS = '=',
  NOT_EQUALS = '<>',
  GREATER_THAN = '>',
  LESS_THAN = '<',
  GREATER_THAN_OR_EQUALS = '>=',
  LESS_THAN_OR_EQUALS = '<=',
  LIKE = 'LIKE',
  ILIKE = 'ILIKE',
  IN = 'IN',
  NOT_IN = 'NOT IN',
  IS_NULL = 'IS NULL',
  IS_NOT_NULL = 'IS NOT NULL',
  BETWEEN = 'BETWEEN',
  NOT_BETWEEN = 'NOT BETWEEN',
  EXISTS = 'EXISTS',
  NOT_EXISTS = 'NOT EXISTS',
  JSONB_CONTAINS = '@>',
  JSONB_CONTAINED_BY = '<@',
  JSONB_HAS_KEY = '?',
  JSONB_HAS_ALL_KEYS = '?&',
  JSONB_HAS_ANY_KEY = '?|'
}

/**
 * Logical operator for combining conditions
 */
export enum LogicalOperator {
  AND = 'AND',
  OR = 'OR'
}

/**
 * SQL query parameter with name and value
 */
interface QueryParameter {
  name: string;
  value: any;
}

/**
 * SQL condition for WHERE clauses
 */
interface Condition {
  field: string;
  operator: ConditionOperator | string;
  value?: any;
  logical?: LogicalOperator;
  isRaw?: boolean;
}

/**
 * SQL join clause
 */
interface Join {
  type: JoinType;
  table: string;
  alias?: string;
  on: string;
}

/**
 * SQL order by clause
 */
interface OrderBy {
  field: string;
  direction: OrderDirection;
}

/**
 * The query builder class
 */
export class PostgresQueryBuilder {
  private type: 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE' = 'SELECT';
  private fields: string[] = ['*'];
  private distinctFields: string[] = [];
  private tableName: string = '';
  private tableAlias: string = '';
  private joins: Join[] = [];
  private conditions: Condition[] = [];
  private groupByFields: string[] = [];
  private havingConditions: Condition[] = [];
  private orderByFields: OrderBy[] = [];
  private limitValue: number | null = null;
  private offsetValue: number | null = null;
  private returningFields: string[] = [];
  private insertData: Record<string, any> | null = null;
  private updateData: Record<string, any> | null = null;
  private parameters: QueryParameter[] = [];
  private paramCounter: number = 1;
  private withClauses: { name: string; query: PostgresQueryBuilder }[] = [];
  private withRecursive: boolean = false;
  private logger = createComponentLogger('PostgresQueryBuilder');

  /**
   * Begin a new SELECT query
   * 
   * @param fields Fields to select (default: ['*'])
   * @returns This query builder
   */
  select(fields: string[] = ['*']): PostgresQueryBuilder {
    this.type = 'SELECT';
    this.fields = fields;
    return this;
  }

  /**
   * Make the SELECT query distinct
   * 
   * @param fields Fields to apply DISTINCT on
   * @returns This query builder
   */
  distinct(fields: string[] = []): PostgresQueryBuilder {
    this.distinctFields = fields;
    return this;
  }

  /**
   * Begin a new INSERT query
   * 
   * @param tableName Table name
   * @param data Data to insert
   * @returns This query builder
   */
  insert(tableName: string, data: Record<string, any>): PostgresQueryBuilder {
    this.type = 'INSERT';
    this.tableName = tableName;
    this.insertData = data;
    return this;
  }

  /**
   * Begin a new UPDATE query
   * 
   * @param tableName Table name
   * @param data Data to update
   * @returns This query builder
   */
  update(tableName: string, data: Record<string, any>): PostgresQueryBuilder {
    this.type = 'UPDATE';
    this.tableName = tableName;
    this.updateData = data;
    return this;
  }

  /**
   * Begin a new DELETE query
   * 
   * @param tableName Table name
   * @returns This query builder
   */
  delete(tableName: string): PostgresQueryBuilder {
    this.type = 'DELETE';
    this.tableName = tableName;
    return this;
  }

  /**
   * Specify the FROM clause for a SELECT query
   * 
   * @param tableName Table name
   * @param alias Optional table alias
   * @returns This query builder
   */
  from(tableName: string, alias?: string): PostgresQueryBuilder {
    this.tableName = tableName;
    this.tableAlias = alias || '';
    return this;
  }

  /**
   * Add a WITH clause to the query
   * 
   * @param name CTE name
   * @param query Query builder for the CTE
   * @returns This query builder
   */
  with(name: string, query: PostgresQueryBuilder): PostgresQueryBuilder {
    this.withClauses.push({ name, query });
    return this;
  }

  /**
   * Set the WITH clause as recursive
   * 
   * @returns This query builder
   */
  recursive(): PostgresQueryBuilder {
    this.withRecursive = true;
    return this;
  }

  /**
   * Add a JOIN clause to the query
   * 
   * @param type Join type
   * @param table Table to join
   * @param on Join condition
   * @param alias Optional table alias
   * @returns This query builder
   */
  join(type: JoinType, table: string, on: string, alias?: string): PostgresQueryBuilder {
    this.joins.push({
      type,
      table,
      on,
      alias
    });
    return this;
  }

  /**
   * Add an INNER JOIN to the query
   * 
   * @param table Table to join
   * @param on Join condition
   * @param alias Optional table alias
   * @returns This query builder
   */
  innerJoin(table: string, on: string, alias?: string): PostgresQueryBuilder {
    return this.join(JoinType.INNER, table, on, alias);
  }

  /**
   * Add a LEFT JOIN to the query
   * 
   * @param table Table to join
   * @param on Join condition
   * @param alias Optional table alias
   * @returns This query builder
   */
  leftJoin(table: string, on: string, alias?: string): PostgresQueryBuilder {
    return this.join(JoinType.LEFT, table, on, alias);
  }

  /**
   * Add a RIGHT JOIN to the query
   * 
   * @param table Table to join
   * @param on Join condition
   * @param alias Optional table alias
   * @returns This query builder
   */
  rightJoin(table: string, on: string, alias?: string): PostgresQueryBuilder {
    return this.join(JoinType.RIGHT, table, on, alias);
  }

  /**
   * Add a FULL JOIN to the query
   * 
   * @param table Table to join
   * @param on Join condition
   * @param alias Optional table alias
   * @returns This query builder
   */
  fullJoin(table: string, on: string, alias?: string): PostgresQueryBuilder {
    return this.join(JoinType.FULL, table, on, alias);
  }

  /**
   * Add a CROSS JOIN to the query
   * 
   * @param table Table to join
   * @param alias Optional table alias
   * @returns This query builder
   */
  crossJoin(table: string, alias?: string): PostgresQueryBuilder {
    return this.join(JoinType.CROSS, table, '1=1', alias);
  }

  /**
   * Add a WHERE condition to the query
   * 
   * @param field Field name
   * @param operator Condition operator
   * @param value Value (optional for IS NULL/IS NOT NULL)
   * @param logical Logical operator (default: AND)
   * @returns This query builder
   */
  where(
    field: string,
    operator: ConditionOperator | string,
    value?: any,
    logical: LogicalOperator = LogicalOperator.AND
  ): PostgresQueryBuilder {
    this.conditions.push({
      field,
      operator,
      value,
      logical: this.conditions.length === 0 ? undefined : logical
    });
    return this;
  }

  /**
   * Add a WHERE condition with AND logic
   * 
   * @param field Field name
   * @param operator Condition operator
   * @param value Value
   * @returns This query builder
   */
  andWhere(field: string, operator: ConditionOperator | string, value?: any): PostgresQueryBuilder {
    return this.where(field, operator, value, LogicalOperator.AND);
  }

  /**
   * Add a WHERE condition with OR logic
   * 
   * @param field Field name
   * @param operator Condition operator
   * @param value Value
   * @returns This query builder
   */
  orWhere(field: string, operator: ConditionOperator | string, value?: any): PostgresQueryBuilder {
    return this.where(field, operator, value, LogicalOperator.OR);
  }

  /**
   * Add a raw WHERE condition to the query
   * 
   * @param rawCondition Raw SQL condition
   * @param logical Logical operator (default: AND)
   * @returns This query builder
   */
  whereRaw(rawCondition: string, logical: LogicalOperator = LogicalOperator.AND): PostgresQueryBuilder {
    this.conditions.push({
      field: rawCondition,
      operator: '',
      logical: this.conditions.length === 0 ? undefined : logical,
      isRaw: true
    });
    return this;
  }

  /**
   * Add a GROUP BY clause to the query
   * 
   * @param fields Fields to group by
   * @returns This query builder
   */
  groupBy(...fields: string[]): PostgresQueryBuilder {
    this.groupByFields = [...this.groupByFields, ...fields];
    return this;
  }

  /**
   * Add a HAVING condition to the query
   * 
   * @param field Field name
   * @param operator Condition operator
   * @param value Value (optional for IS NULL/IS NOT NULL)
   * @param logical Logical operator (default: AND)
   * @returns This query builder
   */
  having(
    field: string,
    operator: ConditionOperator | string,
    value?: any,
    logical: LogicalOperator = LogicalOperator.AND
  ): PostgresQueryBuilder {
    this.havingConditions.push({
      field,
      operator,
      value,
      logical: this.havingConditions.length === 0 ? undefined : logical
    });
    return this;
  }

  /**
   * Add an ORDER BY clause to the query
   * 
   * @param field Field to order by
   * @param direction Order direction (default: ASC)
   * @returns This query builder
   */
  orderBy(field: string, direction: OrderDirection = OrderDirection.ASC): PostgresQueryBuilder {
    this.orderByFields.push({
      field,
      direction
    });
    return this;
  }

  /**
   * Add a LIMIT clause to the query
   * 
   * @param limit Maximum number of rows to return
   * @returns This query builder
   */
  limit(limit: number): PostgresQueryBuilder {
    this.limitValue = limit;
    return this;
  }

  /**
   * Add an OFFSET clause to the query
   * 
   * @param offset Number of rows to skip
   * @returns This query builder
   */
  offset(offset: number): PostgresQueryBuilder {
    this.offsetValue = offset;
    return this;
  }

  /**
   * Add a RETURNING clause to INSERT, UPDATE, or DELETE queries
   * 
   * @param fields Fields to return (default: ['*'])
   * @returns This query builder
   */
  returning(fields: string[] = ['*']): PostgresQueryBuilder {
    this.returningFields = fields;
    return this;
  }

  /**
   * Build the SQL query
   * 
   * @returns SQL query string
   */
  buildQuery(): string {
    try {
      let query = '';

      // Build WITH clause if any
      if (this.withClauses.length > 0) {
        query += 'WITH ';
        if (this.withRecursive) {
          query += 'RECURSIVE ';
        }
        
        const withParts: string[] = [];
        for (const withClause of this.withClauses) {
          withParts.push(`${withClause.name} AS (${withClause.query.buildQuery()})`);
        }
        query += withParts.join(', ') + ' ';
      }

      switch (this.type) {
        case 'SELECT':
          query += this.buildSelectQuery();
          break;
        case 'INSERT':
          query += this.buildInsertQuery();
          break;
        case 'UPDATE':
          query += this.buildUpdateQuery();
          break;
        case 'DELETE':
          query += this.buildDeleteQuery();
          break;
      }

      this.logger.debug(`Built query: ${query}`);
      return query;
    } catch (error: any) {
      this.logger.error('Error building query', error);
      throw new QueryException('Error building query: ' + error.message);
    }
  }

  /**
   * Get the query parameters
   * 
   * @returns Array of parameter values
   */
  getParameters(): any[] {
    return this.parameters.map(param => param.value);
  }

  /**
   * Add a parameter to the query
   * 
   * @param value Parameter value
   * @returns Parameter placeholder (e.g., $1)
   */
  private addParameter(value: any): string {
    const name = `$${this.paramCounter++}`;
    this.parameters.push({ name, value });
    return name;
  }

  /**
   * Build a SELECT query
   * 
   * @returns SQL query string
   */
  private buildSelectQuery(): string {
    if (!this.tableName) {
      throw new QueryException('Table name is required for SELECT queries');
    }

    let query = 'SELECT ';

    // Add DISTINCT if needed
    if (this.distinctFields.length > 0) {
      query += 'DISTINCT ON (' + this.distinctFields.join(', ') + ') ';
    }

    // Add fields
    query += this.fields.join(', ');

    // Add FROM clause
    query += ` FROM ${this.tableName}`;
    if (this.tableAlias) {
      query += ` AS ${this.tableAlias}`;
    }

    // Add JOIN clauses
    for (const join of this.joins) {
      query += ` ${join.type} ${join.table}`;
      if (join.alias) {
        query += ` AS ${join.alias}`;
      }
      query += ` ON ${join.on}`;
    }

    // Add WHERE clause
    const whereClause = this.buildWhereClause();
    if (whereClause) {
      query += ` WHERE ${whereClause}`;
    }

    // Add GROUP BY clause
    if (this.groupByFields.length > 0) {
      query += ` GROUP BY ${this.groupByFields.join(', ')}`;
    }

    // Add HAVING clause
    if (this.havingConditions.length > 0) {
      query += ' HAVING ';
      const havingClause = this.havingConditions.map((condition, index) => {
        let clausePart = '';
        if (index > 0) {
          clausePart = `${condition.logical} `;
        }

        if (condition.isRaw) {
          clausePart += condition.field;
        } else {
          if ([ConditionOperator.IS_NULL, ConditionOperator.IS_NOT_NULL].includes(condition.operator as ConditionOperator)) {
            clausePart += `${condition.field} ${condition.operator}`;
          } else {
            const paramPlaceholder = this.addParameter(condition.value);
            clausePart += `${condition.field} ${condition.operator} ${paramPlaceholder}`;
          }
        }
        return clausePart;
      }).join(' ');
      query += havingClause;
    }

    // Add ORDER BY clause
    if (this.orderByFields.length > 0) {
      query += ` ORDER BY ${this.orderByFields.map(order => `${order.field} ${order.direction}`).join(', ')}`;
    }

    // Add LIMIT clause
    if (this.limitValue !== null) {
      query += ` LIMIT ${this.limitValue}`;
    }

    // Add OFFSET clause
    if (this.offsetValue !== null) {
      query += ` OFFSET ${this.offsetValue}`;
    }

    return query;
  }

  /**
   * Build an INSERT query
   * 
   * @returns SQL query string
   */
  private buildInsertQuery(): string {
    if (!this.tableName) {
      throw new QueryException('Table name is required for INSERT queries');
    }

    if (!this.insertData || Object.keys(this.insertData).length === 0) {
      throw new QueryException('Data is required for INSERT queries');
    }

    const columns = Object.keys(this.insertData);
    const values: string[] = [];

    for (const key of columns) {
      const value = this.insertData[key];
      values.push(this.addParameter(value));
    }

    let query = `INSERT INTO ${this.tableName} (${columns.join(', ')}) VALUES (${values.join(', ')})`;

    // Add RETURNING clause
    if (this.returningFields.length > 0) {
      query += ` RETURNING ${this.returningFields.join(', ')}`;
    }

    return query;
  }

  /**
   * Build an UPDATE query
   * 
   * @returns SQL query string
   */
  private buildUpdateQuery(): string {
    if (!this.tableName) {
      throw new QueryException('Table name is required for UPDATE queries');
    }

    if (!this.updateData || Object.keys(this.updateData).length === 0) {
      throw new QueryException('Data is required for UPDATE queries');
    }

    const setParts: string[] = [];
    for (const [key, value] of Object.entries(this.updateData)) {
      const paramPlaceholder = this.addParameter(value);
      setParts.push(`${key} = ${paramPlaceholder}`);
    }

    let query = `UPDATE ${this.tableName} SET ${setParts.join(', ')}`;

    // Add WHERE clause (essential for updates)
    const whereClause = this.buildWhereClause();
    if (whereClause) {
      query += ` WHERE ${whereClause}`;
    }

    // Add RETURNING clause
    if (this.returningFields.length > 0) {
      query += ` RETURNING ${this.returningFields.join(', ')}`;
    }

    return query;
  }

  /**
   * Build a DELETE query
   * 
   * @returns SQL query string
   */
  private buildDeleteQuery(): string {
    if (!this.tableName) {
      throw new QueryException('Table name is required for DELETE queries');
    }

    let query = `DELETE FROM ${this.tableName}`;

    // Add WHERE clause (essential for deletes)
    const whereClause = this.buildWhereClause();
    if (whereClause) {
      query += ` WHERE ${whereClause}`;
    }

    // Add RETURNING clause
    if (this.returningFields.length > 0) {
      query += ` RETURNING ${this.returningFields.join(', ')}`;
    }

    return query;
  }

  /**
   * Build the WHERE clause
   * 
   * @returns WHERE clause string
   */
  private buildWhereClause(): string {
    if (this.conditions.length === 0) {
      return '';
    }

    return this.conditions.map((condition, index) => {
      let clausePart = '';
      if (index > 0) {
        clausePart = `${condition.logical} `;
      }

      if (condition.isRaw) {
        clausePart += condition.field;
      } else {
        if ([ConditionOperator.IS_NULL, ConditionOperator.IS_NOT_NULL].includes(condition.operator as ConditionOperator)) {
          clausePart += `${condition.field} ${condition.operator}`;
        } else if ([ConditionOperator.IN, ConditionOperator.NOT_IN].includes(condition.operator as ConditionOperator)) {
          const values = condition.value as any[];
          const paramPlaceholders = values.map(val => this.addParameter(val));
          clausePart += `${condition.field} ${condition.operator} (${paramPlaceholders.join(', ')})`;
        } else if ([ConditionOperator.BETWEEN, ConditionOperator.NOT_BETWEEN].includes(condition.operator as ConditionOperator)) {
          const [min, max] = condition.value as [any, any];
          const minParam = this.addParameter(min);
          const maxParam = this.addParameter(max);
          clausePart += `${condition.field} ${condition.operator} ${minParam} AND ${maxParam}`;
        } else {
          const paramPlaceholder = this.addParameter(condition.value);
          clausePart += `${condition.field} ${condition.operator} ${paramPlaceholder}`;
        }
      }
      return clausePart;
    }).join(' ');
  }

  /**
   * Clone this query builder
   * 
   * @returns A new instance of the query builder with the same properties
   */
  clone(): PostgresQueryBuilder {
    const clone = new PostgresQueryBuilder();
    clone.type = this.type;
    clone.fields = [...this.fields];
    clone.distinctFields = [...this.distinctFields];
    clone.tableName = this.tableName;
    clone.tableAlias = this.tableAlias;
    clone.joins = [...this.joins];
    clone.conditions = [...this.conditions];
    clone.groupByFields = [...this.groupByFields];
    clone.havingConditions = [...this.havingConditions];
    clone.orderByFields = [...this.orderByFields];
    clone.limitValue = this.limitValue;
    clone.offsetValue = this.offsetValue;
    clone.returningFields = [...this.returningFields];
    clone.insertData = this.insertData ? { ...this.insertData } : null;
    clone.updateData = this.updateData ? { ...this.updateData } : null;
    clone.parameters = [...this.parameters];
    clone.paramCounter = this.paramCounter;
    clone.withClauses = [...this.withClauses];
    clone.withRecursive = this.withRecursive;
    return clone;
  }
} 