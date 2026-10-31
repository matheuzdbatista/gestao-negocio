from django.contrib import admin
from django.urls import path

from gestao.views import (
    ajuste_estoque,
    cancelar_venda,
    confirmar_venda,
    dashboard,
    detalhe_venda,
    editar_cliente,
    editar_produto,
    entradas_estoque,
    historico_estoque,
    lista_caixa,
    lista_clientes,
    lista_produtos,
    lista_vendas,
    nova_venda,
    novo_cliente,
    novo_movimento,
    novo_produto,
)


urlpatterns = [
    # Painel administrativo
    path(
        "admin/",
        admin.site.urls,
    ),

    # Dashboard
    path(
        "",
        dashboard,
        name="dashboard",
    ),

    # Produtos
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

    # Clientes
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

    # Vendas
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
        "vendas/<int:pk>/",
        detalhe_venda,
        name="detalhe_venda",
    ),
    path(
        "vendas/<int:pk>/confirmar/",
        confirmar_venda,
        name="confirmar_venda",
    ),
    path(
        "vendas/<int:pk>/cancelar/",
        cancelar_venda,
        name="cancelar_venda",
    ),

    # Caixa
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

    # Estoque
    path(
        "estoque/entradas/",
        entradas_estoque,
        name="entradas_estoque",
    ),
    path(
        "estoque/historico/",
        historico_estoque,
        name="historico_estoque",
    ),
    path(
        "estoque/ajuste/",
        ajuste_estoque,
        name="ajuste_estoque",
    ),
]