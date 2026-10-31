from django.contrib import admin
from django.urls import path

from gestao.views import dashboard, lista_produtos, novo_produto


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("produtos/", lista_produtos, name="lista_produtos"),
    path("produtos/novo/", novo_produto, name="novo_produto"),
]