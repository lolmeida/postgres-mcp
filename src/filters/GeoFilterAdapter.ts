/**
 * GeoFilterAdapter
 * 
 * Adaptador para operações de filtro com tipos geométricos do PostgreSQL.
 * Suporta operações com Point, LineString, Polygon e outros tipos geométricos
 * usando a extensão PostGIS.
 */

import { FilterOperator } from './FilterParser';
import { createComponentLogger } from '../utils/logger';

const logger = createComponentLogger('GeoFilterAdapter');

/**
 * Representa um ponto geográfico com latitude e longitude
 */
export interface GeoPoint {
  lat: number;
  lng: number;
}

/**
 * Representa uma caixa delimitadora (bounding box) com dois pontos
 */
export interface GeoBoundingBox {
  min: GeoPoint;
  max: GeoPoint;
}

/**
 * Interface para representar operações com tipos geométricos no PostgreSQL
 */
export interface GeoFilterOptions {
  /**
   * Verifica se a geometria contém outra geometria
   * @example { contains: 'POINT(1 1)' } => column ~ ST_GeomFromText('POINT(1 1)')
   */
  contains?: string | GeoPoint;
  
  /**
   * Verifica se a geometria está contida em outra geometria
   * @example { contained_by: 'POLYGON((0 0, 0 2, 2 2, 2 0, 0 0))' } => column @ ST_GeomFromText('POLYGON((0 0, 0 2, 2 2, 2 0, 0 0))')
   */
  contained_by?: string | GeoBoundingBox;
  
  /**
   * Verifica se a geometria se sobrepõe com outra geometria
   * @example { overlaps: 'LINESTRING(1 1, 2 2)' } => column && ST_GeomFromText('LINESTRING(1 1, 2 2)')
   */
  overlaps?: string;
  
  /**
   * Verifica se a geometria está dentro de uma distância específica de outra geometria
   * @example { distance: { point: {lat: 1, lng: 1}, max: 1000 } } => ST_DWithin(column, ST_MakePoint(1, 1), 1000)
   */
  distance?: {
    point: GeoPoint;
    max: number;
    min?: number;
  };
  
  /**
   * Verifica se a geometria está dentro de um círculo
   * @example { within_circle: { center: {lat: 0, lng: 0}, radius: 1000 } }
   */
  within_circle?: {
    center: GeoPoint;
    radius: number;
  };
  
  /**
   * Verifica se a geometria está dentro de uma área (bounding box)
   * @example { within_box: { min: {lat: 0, lng: 0}, max: {lat: 1, lng: 1} } }
   */
  within_box?: GeoBoundingBox;
  
  /**
   * Calcula a distância entre geometrias e verifica se está dentro de um intervalo
   * @example { st_distance: { geometry: 'POINT(1 1)', lt: 1000 } }
   */
  st_distance?: {
    geometry: string | GeoPoint;
    lt?: number;
    gt?: number;
    lte?: number;
    gte?: number;
    equals?: number;
  };
  
  /**
   * Converte um ponto para um sistema de coordenadas específico
   * Útil quando as coordenadas precisam ser transformadas antes da comparação
   * @example { srid: 4326 }
   */
  srid?: number;
}

/**
 * Classe de adaptador para filtros geométricos PostgreSQL
 */
export class GeoFilterAdapter {
  /**
   * Converte filtros geométricos JSON para formato interno de filtro
   * 
   * @param field Nome do campo
   * @param options Opções de filtro geométrico
   * @returns Objeto de filtro no formato interno
   */
  public static adaptGeoFilter(field: string, options: GeoFilterOptions): any {
    const result: any = {};
    
    if (typeof options !== 'object' || options === null) {
      throw new Error(`Filtro geométrico inválido para o campo ${field}: ${JSON.stringify(options)}`);
    }
    
    // Determina o SRID a ser usado (padrão é 4326 - WGS84, usado por GPS)
    const srid = options.srid || 4326;
    
    // Processa cada operador geométrico
    if (options.contains !== undefined) {
      const geomValue = this.parseGeometry(options.contains, srid);
      result[field] = { [FilterOperator.GEO_CONTAINS]: geomValue };
    }
    
    if (options.contained_by !== undefined) {
      const geomValue = this.parseGeometry(options.contained_by, srid);
      result[field] = { 
        ...(result[field] || {}), 
        [FilterOperator.GEO_CONTAINED_BY]: geomValue 
      };
    }
    
    if (options.overlaps !== undefined) {
      result[field] = { 
        ...(result[field] || {}), 
        [FilterOperator.GEO_OVERLAPS]: options.overlaps 
      };
    }
    
    if (options.distance !== undefined) {
      if (!options.distance.point || typeof options.distance.max !== 'number') {
        throw new Error(`Filtro distance requer 'point' e 'max': ${JSON.stringify(options.distance)}`);
      }
      
      const point = this.pointToWKT(options.distance.point, srid);
      
      if (options.distance.min !== undefined) {
        // Se temos min e max, precisamos criar uma expressão personalizada
        // ST_DWithin(geom, point, max) AND NOT ST_DWithin(geom, point, min)
        result[`ST_DWithin(${field}, ${point}, ${options.distance.max})`] = true;
        result[`NOT ST_DWithin(${field}, ${point}, ${options.distance.min})`] = true;
      } else {
        // Caso simples: apenas distância máxima
        result[field] = { 
          [FilterOperator.GEO_DISTANCE]: {
            point: point,
            distance: options.distance.max
          }
        };
      }
    }
    
    if (options.within_circle !== undefined) {
      if (!options.within_circle.center || !options.within_circle.radius) {
        throw new Error(`Filtro within_circle requer 'center' e 'radius': ${JSON.stringify(options.within_circle)}`);
      }
      
      const center = this.pointToWKT(options.within_circle.center, srid);
      // ST_DWithin(geom, center, radius)
      result[`ST_DWithin(${field}, ${center}, ${options.within_circle.radius})`] = true;
    }
    
    if (options.within_box !== undefined) {
      if (!options.within_box.min || !options.within_box.max) {
        throw new Error(`Filtro within_box requer 'min' e 'max': ${JSON.stringify(options.within_box)}`);
      }
      
      // Cria um polígono de bbox e usa contained_by
      const bbox = this.boundingBoxToWKT(options.within_box, srid);
      result[`ST_Within(${field}, ${bbox})`] = true;
    }
    
    if (options.st_distance !== undefined) {
      if (!options.st_distance.geometry) {
        throw new Error(`Filtro st_distance requer 'geometry': ${JSON.stringify(options.st_distance)}`);
      }
      
      const geom = this.parseGeometry(options.st_distance.geometry, srid);
      const baseExpr = `ST_Distance(${field}, ${geom})`;
      
      if (options.st_distance.equals !== undefined) {
        result[baseExpr] = options.st_distance.equals;
      }
      
      if (options.st_distance.lt !== undefined) {
        result[baseExpr] = { [FilterOperator.LESS_THAN]: options.st_distance.lt };
      }
      
      if (options.st_distance.gt !== undefined) {
        result[baseExpr] = { [FilterOperator.GREATER_THAN]: options.st_distance.gt };
      }
      
      if (options.st_distance.lte !== undefined) {
        result[baseExpr] = { [FilterOperator.LESS_THAN_EQUALS]: options.st_distance.lte };
      }
      
      if (options.st_distance.gte !== undefined) {
        result[baseExpr] = { [FilterOperator.GREATER_THAN_EQUALS]: options.st_distance.gte };
      }
    }
    
    return result;
  }
  
  /**
   * Converte um ponto para formato WKT (Well-Known Text)
   * 
   * @param point Ponto a ser convertido
   * @param srid Sistema de referência espacial
   * @returns String no formato ST_GeomFromText
   */
  private static pointToWKT(point: GeoPoint, srid: number): string {
    return `ST_SetSRID(ST_MakePoint(${point.lng}, ${point.lat}), ${srid})`;
  }
  
  /**
   * Converte uma bounding box para formato WKT (Well-Known Text)
   * 
   * @param bbox Bounding box a ser convertida
   * @param srid Sistema de referência espacial
   * @returns String no formato ST_GeomFromText
   */
  private static boundingBoxToWKT(bbox: GeoBoundingBox, srid: number): string {
    const { min, max } = bbox;
    return `ST_SetSRID(ST_MakeBox2D(
      ST_MakePoint(${min.lng}, ${min.lat}), 
      ST_MakePoint(${max.lng}, ${max.lat})
    ), ${srid})`;
  }
  
  /**
   * Converte diferentes formatos de geometria para WKT
   * 
   * @param geometry Geometria a ser convertida (string WKT ou objeto de ponto/bbox)
   * @param srid Sistema de referência espacial
   * @returns String no formato ST_GeomFromText
   */
  private static parseGeometry(geometry: string | GeoPoint | GeoBoundingBox, srid: number): string {
    if (typeof geometry === 'string') {
      // Assume que já é uma string WKT
      if (geometry.toUpperCase().startsWith('POINT') || 
          geometry.toUpperCase().startsWith('LINESTRING') ||
          geometry.toUpperCase().startsWith('POLYGON')) {
        return `ST_GeomFromText('${geometry}', ${srid})`;
      }
      return geometry; // Assume que já é uma expressão SQL válida
    }
    
    if ('lat' in geometry && 'lng' in geometry) {
      return this.pointToWKT(geometry, srid);
    }
    
    if ('min' in geometry && 'max' in geometry) {
      return this.boundingBoxToWKT(geometry, srid);
    }
    
    logger.warn(`Formato de geometria não reconhecido: ${JSON.stringify(geometry)}`);
    throw new Error(`Formato de geometria não reconhecido: ${JSON.stringify(geometry)}`);
  }
  
  /**
   * Verifica se um objeto é um filtro geométrico válido
   * 
   * @param obj Objeto a ser verificado
   * @returns Verdadeiro se for um filtro geométrico válido
   */
  public static isGeoFilter(obj: any): boolean {
    if (typeof obj !== 'object' || obj === null) {
      return false;
    }
    
    const geoFilterKeys = [
      'contains', 
      'contained_by', 
      'overlaps',
      'distance',
      'within_circle',
      'within_box',
      'st_distance',
      'srid'
    ];
    
    return geoFilterKeys.some(key => key in obj);
  }
} 