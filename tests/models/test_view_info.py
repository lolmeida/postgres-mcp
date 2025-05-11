"""
Testes para o modelo ViewInfo
"""

import pytest
from pydantic import ValidationError

from postgres_mcp.models.base import ColumnInfo, ViewInfo


def test_view_info_valid():
    """Testa a criação de ViewInfo com dados válidos."""
    columns = [
        ColumnInfo(
            name="id", data_type="integer", nullable=False, is_primary=True
        ),
        ColumnInfo(
            name="name", data_type="varchar", nullable=False
        )
    ]
    
    view = ViewInfo(
        name="test_view",
        schema="public",
        columns=columns,
        definition="SELECT id, name FROM users",
        is_materialized=False
    )
    
    assert view.name == "test_view"
    assert view.schema == "public"
    assert len(view.columns) == 2
    assert view.definition == "SELECT id, name FROM users"
    assert view.is_materialized is False
    assert view.comment is None
    assert view.depends_on == []


def test_view_info_materialized():
    """Testa a criação de ViewInfo materializada."""
    columns = [
        ColumnInfo(
            name="id", data_type="integer", nullable=False
        )
    ]
    
    view = ViewInfo(
        name="test_materialized",
        schema="public",
        columns=columns,
        definition="SELECT id FROM users",
        is_materialized=True,
        depends_on=["public.users"]
    )
    
    assert view.name == "test_materialized"
    assert view.is_materialized is True
    assert view.depends_on == ["public.users"]


def test_view_info_missing_required():
    """Testa a criação de ViewInfo sem campos obrigatórios."""
    with pytest.raises(ValidationError):
        ViewInfo(
            schema="public",
            columns=[],
            definition="SELECT * FROM table"
        )
    
    with pytest.raises(ValidationError):
        ViewInfo(
            name="test_view",
            schema="public",
            definition="SELECT * FROM table"
        )
    
    with pytest.raises(ValidationError):
        ViewInfo(
            name="test_view",
            schema="public",
            columns=[]
        )


def test_view_info_defaults():
    """Testa os valores padrão de ViewInfo."""
    columns = [
        ColumnInfo(
            name="id", data_type="integer", nullable=False
        )
    ]
    
    view = ViewInfo(
        name="test_view",
        columns=columns,
        definition="SELECT id FROM users"
    )
    
    assert view.schema == "public"  # valor padrão
    assert view.is_materialized is False  # valor padrão
    assert view.comment is None  # valor padrão
    assert view.depends_on == []  # valor padrão 