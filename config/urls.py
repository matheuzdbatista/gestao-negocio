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
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("produtos/", lista_produtos, name="lista_produtos"),
    path("produtos/novo/", novo_produto, name="novo_produto"),
    path(
        "produtos/<int:pk>/editar/",
        editar_produto,
        name="editar_produto",
    ),
    path("clientes/", lista_clientes, name="lista_clientes"),
    path("clientes/novo/", novo_cliente, name="novo_cliente"),
    path(
        "clientes/<int:pk>/editar/",
        editar_cliente,
        name="editar_cliente",
    ),
]