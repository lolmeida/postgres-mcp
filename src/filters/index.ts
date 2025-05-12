/**
 * Filters Index
 * 
 * Exporta todas as classes e interfaces relacionadas ao sistema de filtros.
 */

// FilterParser - Parser principal de filtros JSON para SQL
export { 
  FilterParser, 
  FilterOperator, 
  FilterParserResult, 
  SQLParameter,
  and,
  or,
  not,
  AndFilter,
  OrFilter,
  NotFilter
} from './FilterParser';

// ArrayFilterAdapter - Adaptador para filtros de arrays
export {
  ArrayFilterAdapter,
  ArrayFilterOptions
} from './ArrayFilterAdapter';

// JSONBFilterAdapter - Adaptador para filtros JSONB
export {
  JSONBFilterAdapter,
  JSONBFilterOptions
} from './JSONBFilterAdapter';

// GeoFilterAdapter - Adaptador para filtros geométricos
export {
  GeoFilterAdapter,
  GeoFilterOptions,
  GeoPoint,
  GeoBoundingBox
} from './GeoFilterAdapter';

// FilterBuilder - Builder para construção de filtros
export {
  FilterBuilder,
  FilterBuilderOptions
} from './FilterBuilder'; 