from django.contrib import admin
from django.urls import path

from gestao.views import (
    dashboard,
    lista_produtos,
    novo_produto,
    editar_produto,
    lista_clientes,
    novo_cliente,
    editar_cliente,
    lista_vendas,
    nova_venda,
    confirmar_venda,
    lista_caixa,
    novo_movimento,
)


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", dashboard, name="dashboard"),

    path(
        "produtos/",
        lista_produtos,
        name="lista_produtos",
    ),
    path(
        "produtos/novo/",
        novo_produto,
        name="novo_produto",
    ),
    path(
        "produtos/<int:pk>/editar/",
        editar_produto,
        name="editar_produto",
    ),

    path(
        "clientes/",
        lista_clientes,
        name="lista_clientes",
    ),
    path(
        "clientes/novo/",
        novo_cliente,
        name="novo_cliente",
    ),
    path(
        "clientes/<int:pk>/editar/",
        editar_cliente,
        name="editar_cliente",
    ),

    path(
        "vendas/",
        lista_vendas,
        name="lista_vendas",
    ),
    path(
        "vendas/nova/",
        nova_venda,
        name="nova_venda",
    ),
    path(
        "vendas/<int:pk>/confirmar/",
        confirmar_venda,
        name="confirmar_venda",
    ),

    path(
        "caixa/",
        lista_caixa,
        name="lista_caixa",
    ),
    path(
        "caixa/novo/",
        novo_movimento,
        name="novo_movimento",
    ),
]