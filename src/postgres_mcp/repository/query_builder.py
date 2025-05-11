"""
Construtor de consultas SQL para PostgreSQL
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Union

from postgres_mcp.core.exceptions import QueryError
from postgres_mcp.models.filters import (
    ArrayFilter, ComparisonFilter, FilterOperator, FiltersType,
    GeometricFilter, JsonbFilter, ListFilter, NullFilter, TextFilter
)
from postgres_mcp.utils.pg_types import (
    PostgresTypeConverter, prepare_array, prepare_box_from_string,
    prepare_jsonb, prepare_point_from_string, prepare_polygon_from_string
)


class QueryBuilder:
    """
    Construtor de consultas SQL para PostgreSQL.
    
    Esta classe fornece métodos para converter estruturas como filtros e
    ordenações em cláusulas SQL válidas para PostgreSQL.
    """
    
    def __init__(self):
        self.params: Dict[str, Any] = {}
        self.param_counter = 0
    
    def add_param(self, value: Any) -> str:
        """
        Adiciona um parâmetro à consulta.
        
        Args:
            value: Valor do parâmetro
            
        Returns:
            Nome do parâmetro
        """
        param_name = f"p_{self.param_counter}"
        self.param_counter += 1
        self.params[param_name] = value
        return param_name
    
    def build_select(
        self,
        table: str,
        filters: Optional[FiltersType] = None,
        columns: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        schema: str = "public",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Constrói uma consulta SELECT.
        
        Args:
            table: Nome da tabela
            filters: Filtros para a consulta
            columns: Colunas específicas a retornar
            order_by: Coluna para ordenação
            ascending: Direção da ordenação
            limit: Limite de registros a retornar
            offset: Número de registros a pular
            schema: Nome do schema
            
        Returns:
            Tupla com a consulta SQL e os parâmetros
        """
        self.params = {}
        self.param_counter = 0
        
        # Construção da cláusula SELECT
        select_clause = f"SELECT {self._build_columns(columns)} FROM {schema}.{self._quote_identifier(table)}"
        
        # Construção da cláusula WHERE
        where_clause = ""
        if filters:
            where_sql = self._build_filters(filters)
            if where_sql:
                where_clause = f" WHERE {where_sql}"
        
        # Construção da cláusula ORDER BY
        order_clause = ""
        if order_by:
            direction = "ASC" if ascending else "DESC"
            order_clause = f" ORDER BY {self._quote_identifier(order_by)} {direction}"
        
        # Construção das cláusulas LIMIT e OFFSET
        limit_clause = f" LIMIT {limit}" if limit is not None else ""
        offset_clause = f" OFFSET {offset}" if offset is not None else ""
        
        # Combinação de todas as cláusulas
        query = f"{select_clause}{where_clause}{order_clause}{limit_clause}{offset_clause}"
        
        return query, self.params
    
    def build_count(
        self,
        table: str,
        filters: Optional[FiltersType] = None,
        schema: str = "public",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Constrói uma consulta COUNT.
        
        Args:
            table: Nome da tabela
            filters: Filtros para a consulta
            schema: Nome do schema
            
        Returns:
            Tupla com a consulta SQL e os parâmetros
        """
        self.params = {}
        self.param_counter = 0
        
        # Construção da cláusula SELECT COUNT
        select_clause = f"SELECT COUNT(*) FROM {schema}.{self._quote_identifier(table)}"
        
        # Construção da cláusula WHERE
        where_clause = ""
        if filters:
            where_sql = self._build_filters(filters)
            if where_sql:
                where_clause = f" WHERE {where_sql}"
        
        # Combinação de todas as cláusulas
        query = f"{select_clause}{where_clause}"
        
        return query, self.params
    
    def build_insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Constrói uma consulta INSERT.
        
        Args:
            table: Nome da tabela
            data: Dados a serem inseridos (único registro ou lista)
            returning: Colunas a serem retornadas
            schema: Nome do schema
            
        Returns:
            Tupla com a consulta SQL e os parâmetros
        """
        self.params = {}
        self.param_counter = 0
        
        # Verificação se é um único registro ou múltiplos
        if isinstance(data, dict):
            data_list = [data]
        else:
            data_list = data
        
        if not data_list:
            raise QueryError("Nenhum dado fornecido para inserção")
        
        # Extração das colunas do primeiro registro
        columns = list(data_list[0].keys())
        
        # Construção da cláusula INSERT
        columns_sql = ", ".join(self._quote_identifier(col) for col in columns)
        
        # Construção dos valores para cada registro
        values_parts = []
        for record in data_list:
            values = []
            for col in columns:
                if col in record:
                    param_name = self.add_param(record[col])
                    values.append(f":{param_name}")
                else:
                    values.append("DEFAULT")
            
            values_sql = ", ".join(values)
            values_parts.append(f"({values_sql})")
        
        # Combinação de todos os registros
        all_values_sql = ", ".join(values_parts)
        
        # Construção da cláusula RETURNING
        returning_clause = ""
        if returning:
            returning_sql = ", ".join(self._quote_identifier(col) for col in returning)
            returning_clause = f" RETURNING {returning_sql}"
        
        # Consulta final
        query = f"INSERT INTO {schema}.{self._quote_identifier(table)} ({columns_sql}) VALUES {all_values_sql}{returning_clause}"
        
        return query, self.params
    
    def build_update(
        self,
        table: str,
        filters: FiltersType,
        data: Dict[str, Any],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Constrói uma consulta UPDATE.
        
        Args:
            table: Nome da tabela
            filters: Filtros para selecionar registros a serem atualizados
            data: Dados a serem atualizados
            returning: Colunas a serem retornadas
            schema: Nome do schema
            
        Returns:
            Tupla com a consulta SQL e os parâmetros
        """
        self.params = {}
        self.param_counter = 0
        
        # Construção da cláusula SET
        set_parts = []
        for key, value in data.items():
            param_name = self.add_param(value)
            set_parts.append(f"{self._quote_identifier(key)} = :{param_name}")
        
        set_clause = ", ".join(set_parts)
        
        # Construção da cláusula WHERE
        where_sql = self._build_filters(filters)
        
        # Construção da cláusula RETURNING
        returning_clause = ""
        if returning:
            returning_sql = ", ".join(self._quote_identifier(col) for col in returning)
            returning_clause = f" RETURNING {returning_sql}"
        
        # Consulta final
        query = f"UPDATE {schema}.{self._quote_identifier(table)} SET {set_clause} WHERE {where_sql}{returning_clause}"
        
        return query, self.params
    
    def build_delete(
        self,
        table: str,
        filters: FiltersType,
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Constrói uma consulta DELETE.
        
        Args:
            table: Nome da tabela
            filters: Filtros para selecionar registros a serem excluídos
            returning: Colunas a serem retornadas
            schema: Nome do schema
            
        Returns:
            Tupla com a consulta SQL e os parâmetros
        """
        self.params = {}
        self.param_counter = 0
        
        # Construção da cláusula WHERE
        where_sql = self._build_filters(filters)
        
        # Construção da cláusula RETURNING
        returning_clause = ""
        if returning:
            returning_sql = ", ".join(self._quote_identifier(col) for col in returning)
            returning_clause = f" RETURNING {returning_sql}"
        
        # Consulta final
        query = f"DELETE FROM {schema}.{self._quote_identifier(table)} WHERE {where_sql}{returning_clause}"
        
        return query, self.params
    
    def _build_columns(self, columns: Optional[List[str]]) -> str:
        """
        Constrói a parte de colunas da consulta SELECT.
        
        Args:
            columns: Lista de colunas a serem selecionadas
            
        Returns:
            String de colunas formatada para SQL
        """
        if not columns:
            return "*"
        
        return ", ".join(self._quote_identifier(col) for col in columns)
    
    def _build_filters(self, filters: FiltersType) -> str:
        """
        Constrói a cláusula WHERE a partir dos filtros.
        
        Args:
            filters: Dicionário de filtros
            
        Returns:
            Cláusula WHERE em SQL (sem a palavra-chave WHERE)
        """
        if not filters:
            return ""
        
        conditions = []
        
        for key, value in filters.items():
            condition = self._process_filter(key, value)
            if condition:
                conditions.append(condition)
        
        if not conditions:
            return ""
        
        return " AND ".join(conditions)
    
    def _process_filter(self, key: str, value: Any) -> str:
        """
        Processa um filtro individual.
        
        Args:
            key: Nome da coluna
            value: Valor ou objeto de filtro
            
        Returns:
            Condição SQL para o filtro
        """
        # Filtro de igualdade simples
        if not isinstance(value, dict):
            param_name = self.add_param(value)
            if value is None:
                return f"{self._quote_identifier(key)} IS NULL"
            else:
                return f"{self._quote_identifier(key)} = :{param_name}"
        
        # Verificação se é um filtro complexo ou um objeto aninhado
        if any(key in FilterOperator.__members__.values() for key in value.keys()):
            # É um filtro complexo
            return self._build_complex_filter(key, value)
        else:
            # É um objeto aninhado - recursão para construir condições aninhadas
            nested_conditions = []
            for nested_key, nested_value in value.items():
                full_key = f"{key}.{nested_key}"
                nested_condition = self._process_filter(full_key, nested_value)
                if nested_condition:
                    nested_conditions.append(nested_condition)
            
            if not nested_conditions:
                return ""
            
            return "(" + " AND ".join(nested_conditions) + ")"
    
    def _build_complex_filter(self, key: str, filter_dict: Dict[str, Any]) -> str:
        """
        Constrói uma condição SQL para um filtro complexo.
        
        Args:
            key: Nome da coluna
            filter_dict: Dicionário de filtro complexo
            
        Returns:
            Condição SQL para o filtro complexo
        """
        conditions = []
        
        # Processar cada operador no filtro
        for op_str, value in filter_dict.items():
            # Tratamento especial para o operador "in" (palavra reservada em Python)
            if op_str == "in":
                op_str = "in_"
            
            try:
                # Tentar encontrar o operador na enumeração
                op = FilterOperator(op_str)
            except ValueError:
                # Se não for um operador válido, ignorar
                continue
            
            # Construir a condição com base no tipo de operador
            condition = self._build_operator_condition(key, op, value)
            if condition:
                conditions.append(condition)
        
        if not conditions:
            return ""
        
        return "(" + " AND ".join(conditions) + ")"
    
    def _build_operator_condition(self, key: str, op: FilterOperator, value: Any) -> str:
        """
        Constrói uma condição SQL para um operador específico.
        
        Args:
            key: Nome da coluna
            op: Operador de filtro
            value: Valor para o filtro
            
        Returns:
            Condição SQL para o operador
        """
        quoted_key = self._quote_identifier(key)
        
        # Operadores de comparação
        if op == FilterOperator.EQ:
            if value is None:
                return f"{quoted_key} IS NULL"
            param_name = self.add_param(value)
            return f"{quoted_key} = :{param_name}"
        
        elif op == FilterOperator.NE:
            if value is None:
                return f"{quoted_key} IS NOT NULL"
            param_name = self.add_param(value)
            return f"{quoted_key} <> :{param_name}"
        
        elif op == FilterOperator.GT:
            param_name = self.add_param(value)
            return f"{quoted_key} > :{param_name}"
        
        elif op == FilterOperator.LT:
            param_name = self.add_param(value)
            return f"{quoted_key} < :{param_name}"
        
        elif op == FilterOperator.GTE:
            param_name = self.add_param(value)
            return f"{quoted_key} >= :{param_name}"
        
        elif op == FilterOperator.LTE:
            param_name = self.add_param(value)
            return f"{quoted_key} <= :{param_name}"
        
        # Operadores de texto
        elif op == FilterOperator.LIKE:
            param_name = self.add_param(value)
            return f"{quoted_key} LIKE :{param_name}"
        
        elif op == FilterOperator.ILIKE:
            param_name = self.add_param(value)
            return f"{quoted_key} ILIKE :{param_name}"
        
        elif op == FilterOperator.MATCH:
            param_name = self.add_param(value)
            return f"{quoted_key} ~ :{param_name}"
        
        elif op == FilterOperator.IMATCH:
            param_name = self.add_param(value)
            return f"{quoted_key} ~* :{param_name}"
        
        # Operadores de lista
        elif op == FilterOperator.IN:
            # Verificar se a lista está vazia
            if not value:
                return "FALSE"  # Uma lista vazia para IN sempre resulta em FALSE
            
            param_name = self.add_param(value)
            return f"{quoted_key} = ANY(:{param_name})"
        
        elif op == FilterOperator.NIN:
            # Verificar se a lista está vazia
            if not value:
                return "TRUE"  # Uma lista vazia para NOT IN sempre resulta em TRUE
            
            param_name = self.add_param(value)
            return f"NOT ({quoted_key} = ANY(:{param_name}))"
        
        # Operadores para valores nulos
        elif op == FilterOperator.IS:
            if value == "null":
                return f"{quoted_key} IS NULL"
            elif value == "not null":
                return f"{quoted_key} IS NOT NULL"
            else:
                return ""
        
        # Operadores para arrays
        elif op == FilterOperator.CONTAINS:
            # Melhorar o suporte a arrays para lidar com diferentes tipos de elementos
            array_value = prepare_array(value) if isinstance(value, list) else value
            param_name = self.add_param(array_value)
            return f"{quoted_key} @> :{param_name}"
        
        elif op == FilterOperator.CONTAINED_BY:
            array_value = prepare_array(value) if isinstance(value, list) else value
            param_name = self.add_param(array_value)
            return f"{quoted_key} <@ :{param_name}"
        
        elif op == FilterOperator.OVERLAP:
            array_value = prepare_array(value) if isinstance(value, list) else value
            param_name = self.add_param(array_value)
            return f"{quoted_key} && :{param_name}"
        
        elif op == FilterOperator.ARRAY_LENGTH:
            param_name = self.add_param(value)
            return f"array_length({quoted_key}, 1) = :{param_name}"
        
        elif op == FilterOperator.ARRAY_LENGTH_GT:
            param_name = self.add_param(value)
            return f"array_length({quoted_key}, 1) > :{param_name}"
        
        elif op == FilterOperator.ARRAY_LENGTH_LT:
            param_name = self.add_param(value)
            return f"array_length({quoted_key}, 1) < :{param_name}"
        
        # Operadores para JSON/JSONB
        elif op == FilterOperator.JSONB_CONTAINS:
            # Converter valor para string JSON formatada corretamente
            if isinstance(value, (dict, list)):
                jsonb_value = prepare_jsonb(value)
                param_name = self.add_param(jsonb_value)
                return f"{quoted_key} @> :{param_name}::jsonb"
            else:
                param_name = self.add_param(value)
                return f"{quoted_key} @> :{param_name}::jsonb"
        
        elif op == FilterOperator.JSONB_CONTAINED_BY:
            if isinstance(value, (dict, list)):
                jsonb_value = prepare_jsonb(value)
                param_name = self.add_param(jsonb_value)
                return f"{quoted_key} <@ :{param_name}::jsonb"
            else:
                param_name = self.add_param(value)
                return f"{quoted_key} <@ :{param_name}::jsonb"
        
        elif op == FilterOperator.HAS_KEY:
            param_name = self.add_param(value)
            return f"{quoted_key} ? :{param_name}"
        
        elif op == FilterOperator.HAS_ANY_KEYS:
            # Garantir que value é uma lista de chaves
            if not isinstance(value, list):
                value = [value]
            param_name = self.add_param(value)
            return f"{quoted_key} ?| :{param_name}"
        
        elif op == FilterOperator.HAS_ALL_KEYS:
            # Garantir que value é uma lista de chaves
            if not isinstance(value, list):
                value = [value]
            param_name = self.add_param(value)
            return f"{quoted_key} ?& :{param_name}"
        
        elif op == FilterOperator.JSONB_PATH:
            # Verificar se é uma string ou um objeto de caminho JSONB
            if isinstance(value, dict):
                jsonb_path = prepare_jsonb(value)
                param_name = self.add_param(jsonb_path)
                return f"{quoted_key} @@ :{param_name}::jsonpath"
            else:
                param_name = self.add_param(value)
                return f"{quoted_key} @@ :{param_name}::jsonpath"
        
        # Operadores para tipos geométricos
        elif op == FilterOperator.DISTANCE:
            # Distância entre pontos
            try:
                # Verificar se é um valor numérico direto ou uma string
                if isinstance(value, (int, float)):
                    param_name = self.add_param(value)
                    return f"ST_Distance({quoted_key}, ST_MakePoint(0, 0)) = :{param_name}"
                else:
                    # Espera-se um formato como "ponto:(x,y),distância:d"
                    parts = value.split(",")
                    if len(parts) == 2 and parts[0].startswith("(") and parts[0].endswith(")"):
                        point = parts[0]
                        distance = float(parts[1])
                        point_param = self.add_param(prepare_point_from_string(point))
                        distance_param = self.add_param(distance)
                        return f"ST_Distance({quoted_key}, {point_param}::point) = :{distance_param}"
                    else:
                        # Adicionar apenas o parâmetro original para evitar erro na consulta
                        param_name = self.add_param(value)
                        return f"ST_Distance({quoted_key}, :{param_name}::point) = 0"
            except Exception as e:
                # Em caso de erro, retornar condição sempre falsa
                return "FALSE"
        
        elif op == FilterOperator.NEAR:
            # Ponto próximo (dentro de determinada distância)
            try:
                # Verificar o formato correto: "(x,y)" ou "(x,y),distância"
                if isinstance(value, str):
                    parts = value.split(",")
                    # Extrair ponto e distância
                    if len(parts) >= 2 and parts[0].startswith("(") and ")" in value:
                        # Encontrar o índice do fechamento do parêntese
                        close_paren_idx = value.find(")")
                        point_str = value[:close_paren_idx + 1]
                        
                        # Extrair a distância, padrão 1.0 se não especificada
                        try:
                            distance = float(value[close_paren_idx + 2:])
                        except (ValueError, IndexError):
                            distance = 1.0
                            
                        point_param = self.add_param(prepare_point_from_string(point_str))
                        distance_param = self.add_param(distance)
                        return f"ST_DWithin({quoted_key}, {point_param}::point, :{distance_param})"
                    else:
                        # Formato simples "(x,y)" sem distância especificada
                        point_param = self.add_param(prepare_point_from_string(value))
                        return f"ST_DWithin({quoted_key}, {point_param}::point, 1.0)"
                else:
                    # Valor inesperado, retornar condição sempre falsa
                    return "FALSE"
            except Exception as e:
                # Em caso de erro, retornar condição sempre falsa
                return "FALSE"
        
        elif op == FilterOperator.CONTAINS_POINT:
            # Polígono contém ponto
            try:
                if isinstance(value, str) and value.startswith("(") and value.endswith(")"):
                    point_param = self.add_param(prepare_point_from_string(value))
                    return f"ST_Contains({quoted_key}, {point_param}::point)"
                else:
                    # Valor inesperado, retornar condição sempre falsa
                    return "FALSE"
            except Exception as e:
                # Em caso de erro, retornar condição sempre falsa
                return "FALSE"
        
        elif op == FilterOperator.WITHIN:
            # Ponto/objeto está dentro de outro
            try:
                if isinstance(value, str):
                    if value.startswith("((") and value.endswith("))"):
                        # É uma box
                        box_param = self.add_param(prepare_box_from_string(value))
                        return f"ST_Within({quoted_key}, {box_param}::box)"
                    elif value.startswith("(") and value.endswith(")") and value.count("(") >= 3:
                        # É um polígono
                        polygon_param = self.add_param(prepare_polygon_from_string(value))
                        return f"ST_Within({quoted_key}, {polygon_param}::polygon)"
                    else:
                        # Formato desconhecido, retornar condição sempre falsa
                        return "FALSE"
                else:
                    # Valor inesperado, retornar condição sempre falsa
                    return "FALSE"
            except Exception as e:
                # Em caso de erro, retornar condição sempre falsa
                return "FALSE"
        
        elif op == FilterOperator.INTERSECTS:
            # Objetos se interceptam
            try:
                if isinstance(value, str):
                    if value.startswith("((") and value.endswith("))"):
                        # É uma box
                        box_param = self.add_param(prepare_box_from_string(value))
                        return f"ST_Intersects({quoted_key}, {box_param}::box)"
                    elif value.startswith("(") and value.endswith(")") and value.count("(") >= 3:
                        # É um polígono
                        polygon_param = self.add_param(prepare_polygon_from_string(value))
                        return f"ST_Intersects({quoted_key}, {polygon_param}::polygon)"
                    elif value.startswith("(") and value.endswith(")") and value.count(",") == 1:
                        # É um ponto
                        point_param = self.add_param(prepare_point_from_string(value))
                        return f"ST_Intersects({quoted_key}, {point_param}::point)"
                    else:
                        # Formato desconhecido, retornar condição sempre falsa
                        return "FALSE"
                else:
                    # Valor inesperado, retornar condição sempre falsa
                    return "FALSE"
            except Exception as e:
                # Em caso de erro, retornar condição sempre falsa
                return "FALSE"
        
        elif op == FilterOperator.BOUNDING_BOX:
            # Dentro da caixa delimitadora
            try:
                if isinstance(value, str) and value.startswith("((") and value.endswith("))"):
                    box_param = self.add_param(prepare_box_from_string(value))
                    return f"{quoted_key} <@ {box_param}::box"
                else:
                    # Valor inesperado, retornar condição sempre falsa
                    return "FALSE"
            except Exception as e:
                # Em caso de erro, retornar condição sempre falsa
                return "FALSE"
        
        return ""
    
    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """
        Coloca aspas duplas em um identificador SQL.
        
        Args:
            identifier: Nome do identificador (tabela, coluna, etc.)
            
        Returns:
            Identificador com aspas
        """
        # Substitui aspas duplas por aspas duplas duplicadas para escapar
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"' 