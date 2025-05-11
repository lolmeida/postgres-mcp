"""
Utilitários para tipos de dados avançados do PostgreSQL.

Este módulo fornece funções para trabalhar com tipos de dados específicos
do PostgreSQL, como arrays e JSONB, facilitando a conversão entre tipos
Python e PostgreSQL.
"""

import json
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