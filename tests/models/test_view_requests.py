"""
Testes para os modelos de requisição relacionados a views
"""

import pytest
from pydantic import ValidationError

from postgres_mcp.models.requests import (
    CreateViewRequest, DescribeViewRequest, DropViewRequest,
    ListViewsRequest, ReadViewRequest, RefreshMaterializedViewRequest, ViewReference
)


def test_view_reference_valid():
    """Testa a criação de ViewReference com dados válidos."""
    reference = ViewReference(view="customers_view", schema="sales")
    
    assert reference.view == "customers_view"
    assert reference.schema == "sales"


def test_view_reference_defaults():
    """Testa os valores padrão de ViewReference."""
    reference = ViewReference(view="users_view")
    
    assert reference.view == "users_view"
    assert reference.schema == "public"  # valor padrão


def test_view_reference_validation():
    """Testa a validação de ViewReference."""
    with pytest.raises(ValidationError):
        ViewReference(view="", schema="public")
    
    with pytest.raises(ValidationError):
        ViewReference(view="users_view", schema="")


def test_list_views_request_valid():
    """Testa a criação de ListViewsRequest com dados válidos."""
    request = ListViewsRequest(schema="analytics", include_materialized=False)
    
    assert request.schema == "analytics"
    assert request.include_materialized is False


def test_list_views_request_defaults():
    """Testa os valores padrão de ListViewsRequest."""
    request = ListViewsRequest()
    
    assert request.schema == "public"  # valor padrão
    assert request.include_materialized is True  # valor padrão


def test_describe_view_request_valid():
    """Testa a criação de DescribeViewRequest com dados válidos."""
    request = DescribeViewRequest(view="sales_report", schema="reporting")
    
    assert request.view == "sales_report"
    assert request.schema == "reporting"


def test_read_view_request_valid():
    """Testa a criação de ReadViewRequest com dados válidos."""
    request = ReadViewRequest(
        view="active_users",
        schema="public",
        filters={"age": {"gt": 18}},
        columns=["id", "name", "email"],
        order_by="name",
        ascending=True,
        limit=10,
        offset=0
    )
    
    assert request.view == "active_users"
    assert request.schema == "public"
    assert request.filters == {"age": {"gt": 18}}
    assert request.columns == ["id", "name", "email"]
    assert request.order_by == "name"
    assert request.ascending is True
    assert request.limit == 10
    assert request.offset == 0


def test_read_view_request_defaults():
    """Testa os valores padrão de ReadViewRequest."""
    request = ReadViewRequest(view="customers")
    
    assert request.view == "customers"
    assert request.schema == "public"  # valor padrão
    assert request.filters is None  # valor padrão
    assert request.columns is None  # valor padrão
    assert request.order_by is None  # valor padrão
    assert request.ascending is True  # valor padrão
    assert request.limit is None  # valor padrão
    assert request.offset is None  # valor padrão


def test_read_view_request_validation():
    """Testa a validação de ReadViewRequest."""
    with pytest.raises(ValidationError):
        ReadViewRequest(view="customers", limit=0)
    
    with pytest.raises(ValidationError):
        ReadViewRequest(view="customers", offset=-1)


def test_create_view_request_valid():
    """Testa a criação de CreateViewRequest com dados válidos."""
    request = CreateViewRequest(
        view="monthly_sales",
        schema="reporting",
        definition="SELECT month, SUM(amount) as total FROM sales GROUP BY month",
        is_materialized=True,
        replace=True
    )
    
    assert request.view == "monthly_sales"
    assert request.schema == "reporting"
    assert request.definition == "SELECT month, SUM(amount) as total FROM sales GROUP BY month"
    assert request.is_materialized is True
    assert request.replace is True


def test_create_view_request_defaults():
    """Testa os valores padrão de CreateViewRequest."""
    request = CreateViewRequest(
        view="active_users",
        definition="SELECT * FROM users WHERE active = true"
    )
    
    assert request.view == "active_users"
    assert request.schema == "public"  # valor padrão
    assert request.definition == "SELECT * FROM users WHERE active = true"
    assert request.is_materialized is False  # valor padrão
    assert request.replace is False  # valor padrão


def test_create_view_request_validation():
    """Testa a validação de CreateViewRequest."""
    with pytest.raises(ValidationError):
        CreateViewRequest(
            view="test_view",
            definition=""  # definição vazia
        )


def test_refresh_materialized_view_request_valid():
    """Testa a criação de RefreshMaterializedViewRequest com dados válidos."""
    request = RefreshMaterializedViewRequest(
        view="sales_summary",
        schema="reporting",
        concurrently=True
    )
    
    assert request.view == "sales_summary"
    assert request.schema == "reporting"
    assert request.concurrently is True


def test_refresh_materialized_view_request_defaults():
    """Testa os valores padrão de RefreshMaterializedViewRequest."""
    request = RefreshMaterializedViewRequest(view="daily_stats")
    
    assert request.view == "daily_stats"
    assert request.schema == "public"  # valor padrão
    assert request.concurrently is False  # valor padrão


def test_drop_view_request_valid():
    """Testa a criação de DropViewRequest com dados válidos."""
    request = DropViewRequest(
        view="old_stats",
        schema="reporting",
        if_exists=True,
        cascade=True
    )
    
    assert request.view == "old_stats"
    assert request.schema == "reporting"
    assert request.if_exists is True
    assert request.cascade is True


def test_drop_view_request_defaults():
    """Testa os valores padrão de DropViewRequest."""
    request = DropViewRequest(view="temp_view")
    
    assert request.view == "temp_view"
    assert request.schema == "public"  # valor padrão
    assert request.if_exists is False  # valor padrão
    assert request.cascade is False  # valor padrão 