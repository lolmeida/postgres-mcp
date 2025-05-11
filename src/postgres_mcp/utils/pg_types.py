"""
Utilitários para tipos de dados avançados do PostgreSQL.

Este módulo fornece funções para trabalhar com tipos de dados específicos
do PostgreSQL, como arrays e JSONB, facilitando a conversão entre tipos
Python e PostgreSQL.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import asyncpg


class PostgresTypeConverter:
    """
    Conversor de tipos entre Python e PostgreSQL.
    
    Fornece métodos para converter tipos de dados Python para tipos PostgreSQL,
    e vice-versa, especialmente para tipos avançados como arrays e JSONB.
    """
    
    @staticmethod
    def prepare_array_value(value: List[Any]) -> str:
        """
        Prepara um valor de array Python para uso em uma consulta PostgreSQL.
        
        Args:
            value: Lista Python a ser convertida em string de array PostgreSQL
            
        Returns:
            String formatada para representar um array do PostgreSQL
        """
        if not value:
            return "{}"
        
        # Processar elementos com base em seus tipos
        elements = []
        for elem in value:
            if elem is None:
                elements.append("NULL")
            elif isinstance(elem, (int, float)):
                elements.append(str(elem))
            elif isinstance(elem, bool):
                elements.append("TRUE" if elem else "FALSE")
            elif isinstance(elem, str):
                # Escapar aspas e caracteres especiais
                escaped = elem.replace("\\", "\\\\").replace('"', '\\"')
                elements.append(f'"{escaped}"')
            elif isinstance(elem, list):
                # Recursão para arrays aninhados
                elements.append(PostgresTypeConverter.prepare_array_value(elem))
            elif isinstance(elem, dict):
                # Converter dicionário para JSONB
                json_str = json.dumps(elem)
                elements.append(f'"{json_str.replace("\"", "\\\"")}"')
            else:
                # Tentar converter para string como último recurso
                elements.append(f'"{str(elem)}"')
        
        return "{" + ",".join(elements) + "}"
    
    @staticmethod
    def prepare_jsonb_value(value: Union[Dict[str, Any], List[Any]]) -> str:
        """
        Prepara um valor JSON/JSONB para uso em uma consulta PostgreSQL.
        
        Args:
            value: Dicionário ou lista Python a ser convertido para JSONB
            
        Returns:
            String formatada para representar um valor JSONB
        """
        return json.dumps(value)
    
    @staticmethod
    def validate_point(point_str: str) -> bool:
        """
        Valida se uma string representa um ponto PostgreSQL válido.
        
        Args:
            point_str: String que representa um ponto (x,y)
            
        Returns:
            True se for um ponto válido, False caso contrário
        """
        if not isinstance(point_str, str):
            return False
            
        pattern = r'^\(\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*\)$'
        return bool(re.match(pattern, point_str))
    
    @staticmethod
    def validate_box(box_str: str) -> bool:
        """
        Valida se uma string representa uma box PostgreSQL válida.
        
        Args:
            box_str: String que representa uma box ((x1,y1),(x2,y2))
            
        Returns:
            True se for uma box válida, False caso contrário
        """
        if not isinstance(box_str, str):
            return False
            
        # Verificar formato básico ((x1,y1),(x2,y2))
        if not (box_str.startswith("((") and box_str.endswith("))")):
            return False
            
        # Extrair os dois pontos
        try:
            inner_content = box_str[1:-1]  # Remover parênteses externos
            points = inner_content.split("),(")
            
            if len(points) != 2:
                return False
                
            point1 = "(" + points[0] + ")"
            point2 = "(" + points[1] + ")"
            
            return (PostgresTypeConverter.validate_point(point1) and 
                    PostgresTypeConverter.validate_point(point2))
        except Exception:
            return False
    
    @staticmethod
    def validate_polygon(polygon_str: str) -> bool:
        """
        Valida se uma string representa um polígono PostgreSQL válido.
        
        Args:
            polygon_str: String que representa um polígono ((x1,y1),...,(xn,yn))
            
        Returns:
            True se for um polígono válido, False caso contrário
        """
        if not isinstance(polygon_str, str):
            return False
            
        # Verificar formato básico de um polígono
        if not (polygon_str.startswith("(") and polygon_str.endswith(")")):
            return False
            
        # Remover parênteses externos e dividir pelos pontos
        try:
            # Expressão regular para extrair pontos
            point_pattern = r'\(\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*\)'
            points = re.findall(point_pattern, polygon_str)
            
            # Um polígono válido precisa de pelo menos 3 pontos
            return len(points) >= 3
        except Exception:
            return False
    
    @staticmethod
    def prepare_point(x: float, y: float) -> str:
        """
        Prepara um ponto para uso em uma consulta PostgreSQL.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            String formatada para representar um ponto PostgreSQL
        """
        return f"POINT({x} {y})"
    
    @staticmethod
    def prepare_point_from_string(point_str: str) -> str:
        """
        Converte uma string de ponto no formato (x,y) para POINT(x y).
        
        Args:
            point_str: String no formato (x,y)
            
        Returns:
            String formatada para representar um ponto PostgreSQL
            
        Raises:
            ValueError: Se o formato da string não for válido
        """
        if not PostgresTypeConverter.validate_point(point_str):
            raise ValueError(f"Formato de ponto inválido: {point_str}")
            
        # Extrair coordenadas
        point_content = point_str.strip()[1:-1]  # Remover parênteses
        x, y = map(float, point_content.split(","))
        
        return PostgresTypeConverter.prepare_point(x, y)
    
    @staticmethod
    def prepare_box_from_string(box_str: str) -> str:
        """
        Converte uma string de box no formato ((x1,y1),(x2,y2)) para BOX(x1 y1, x2 y2).
        
        Args:
            box_str: String no formato ((x1,y1),(x2,y2))
            
        Returns:
            String formatada para representar uma box PostgreSQL
            
        Raises:
            ValueError: Se o formato da string não for válido
        """
        if not PostgresTypeConverter.validate_box(box_str):
            raise ValueError(f"Formato de box inválido: {box_str}")
            
        # Extrair pontos
        inner_content = box_str[1:-1]  # Remover parênteses externos
        point_strings = inner_content.split("),(")
        
        # Extrair coordenadas do primeiro ponto
        point1_content = point_strings[0][1:]  # Remover parêntese inicial
        x1, y1 = map(float, point1_content.split(","))
        
        # Extrair coordenadas do segundo ponto
        point2_content = point_strings[1][:-1]  # Remover parêntese final
        x2, y2 = map(float, point2_content.split(","))
        
        return f"BOX({x1} {y1}, {x2} {y2})"
    
    @staticmethod
    def prepare_polygon_from_string(polygon_str: str) -> str:
        """
        Converte uma string de polígono para o formato PostgreSQL.
        
        Args:
            polygon_str: String que representa um polígono
            
        Returns:
            String formatada para representar um polígono PostgreSQL
            
        Raises:
            ValueError: Se o formato da string não for válido
        """
        if not PostgresTypeConverter.validate_polygon(polygon_str):
            raise ValueError(f"Formato de polígono inválido: {polygon_str}")
            
        # Expressão regular para extrair coordenadas dos pontos
        pattern = r'\(\s*(-?\d+(\.\d+)?)\s*,\s*(-?\d+(\.\d+)?)\s*\)'
        matches = re.findall(pattern, polygon_str)
        
        # Formatar pontos para o estilo PostgreSQL: 'x1 y1, x2 y2, ...'
        points = []
        for match in matches:
            x, _, y, _ = match  # Ignorar grupos de captura decimal
            points.append(f"{x} {y}")
            
        # Montar o polígono final
        return f"POLYGON(({', '.join(points)}))"
    
    @staticmethod
    def register_type_handlers(connection_pool: asyncpg.Pool) -> None:
        """
        Registra manipuladores de tipos personalizados no pool de conexões.
        
        Isto é necessário para que o driver asyncpg saiba como lidar com
        tipos avançados como arrays multidimensionais e JSONB.
        
        Args:
            connection_pool: Pool de conexões asyncpg
        """
        async def _init_connection(conn: asyncpg.Connection) -> None:
            # Configurar manipuladores para JSONB
            await conn.set_type_codec(
                'jsonb',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog'
            )
            
            # Configurar manipuladores para JSON
            await conn.set_type_codec(
                'json',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog'
            )
            
            # Outras configurações de tipos personalizados podem ser adicionadas aqui
        
        # Registra a função de inicialização para ser executada em cada conexão
        connection_pool.init(init=_init_connection)
    
    @staticmethod
    async def register_type_handlers_on_connection(conn: asyncpg.Connection) -> None:
        """
        Registra manipuladores de tipos personalizados em uma conexão específica.
        
        Args:
            conn: Conexão asyncpg
        """
        # Configurar manipuladores para JSONB
        await conn.set_type_codec(
            'jsonb',
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog'
        )
        
        # Configurar manipuladores para JSON
        await conn.set_type_codec(
            'json',
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog'
        )


# Funções auxiliares para uso direto

def prepare_array(value: List[Any]) -> str:
    """
    Prepara um valor de array Python para uso em uma consulta PostgreSQL.
    
    Args:
        value: Lista Python a ser convertida
        
    Returns:
        String formatada para representar um array do PostgreSQL
    """
    return PostgresTypeConverter.prepare_array_value(value)


def prepare_jsonb(value: Union[Dict[str, Any], List[Any]]) -> str:
    """
    Prepara um valor JSON/JSONB para uso em uma consulta PostgreSQL.
    
    Args:
        value: Dicionário ou lista Python
        
    Returns:
        String formatada para representar um valor JSONB
    """
    return PostgresTypeConverter.prepare_jsonb_value(value)


def prepare_point(x: float, y: float) -> str:
    """
    Prepara um ponto para uso em uma consulta PostgreSQL.
    
    Args:
        x: Coordenada X
        y: Coordenada Y
        
    Returns:
        String formatada para representar um ponto PostgreSQL
    """
    return PostgresTypeConverter.prepare_point(x, y)


def prepare_point_from_string(point_str: str) -> str:
    """
    Prepara um ponto a partir de uma string no formato (x,y).
    
    Args:
        point_str: String de ponto no formato (x,y)
        
    Returns:
        String formatada para representar um ponto PostgreSQL
    """
    return PostgresTypeConverter.prepare_point_from_string(point_str)


def prepare_box_from_string(box_str: str) -> str:
    """
    Prepara uma box a partir de uma string no formato ((x1,y1),(x2,y2)).
    
    Args:
        box_str: String de box
        
    Returns:
        String formatada para representar uma box PostgreSQL
    """
    return PostgresTypeConverter.prepare_box_from_string(box_str)


def prepare_polygon_from_string(polygon_str: str) -> str:
    """
    Prepara um polígono a partir de uma string.
    
    Args:
        polygon_str: String de polígono
        
    Returns:
        String formatada para representar um polígono PostgreSQL
    """
    return PostgresTypeConverter.prepare_polygon_from_string(polygon_str) 