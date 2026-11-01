from decimal import Decimal

from django.contrib import admin, messages
from django.db import transaction
from django.utils.formats import number_format

from .models import (
    Cliente,
    EntradaEstoque,
    ItemVenda,
    MovimentoCaixa,
    MovimentoEstoque,
    Produto,
    Venda,
)
from .services import confirmar_venda_com_estoque


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = [
        "nome",
        "codigo",
        "preco",
        "estoque",
        "estoque_minimo",
    ]

    search_fields = [
        "nome",
        "codigo",
    ]

    ordering = [
        "nome",
        "id",
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ["estoque"]

        return []

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                # Preserva o estoque, inclusive se houver
                # movimentações durante a edição do cadastro.
                obj.save(
                    update_fields=[
                        "nome",
                        "codigo",
                        "preco",
                        "estoque_minimo",
                    ]
                )
            else:
                super().save_model(
                    request,
                    obj,
                    form,
                    change,
                )

                if obj.estoque > 0:
                    MovimentoEstoque.objects.create(
                        produto=obj,
                        tipo="entrada",
                        origem="inicial",
                        quantidade=obj.estoque,
                        saldo_apos=obj.estoque,
                        motivo=(
                            "Estoque inicial no cadastro "
                            "pelo painel administrativo."
                        ),
                        usuario=request.user,
                    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        "nome",
        "telefone",
        "email",
    ]

    search_fields = [
        "nome",
        "telefone",
        "email",
    ]

    ordering = [
        "nome",
        "id",
    ]


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda

    extra = 1
    min_num = 1
    validate_min = True
    max_num = 20
    validate_max = True

    def has_add_permission(self, request, obj=None):
        if obj and (obj.confirmada or obj.cancelada):
            return False

        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and (obj.confirmada or obj.cancelada):
            return False

        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and (obj.confirmada or obj.cancelada):
            return False

        return super().has_delete_permission(request, obj)


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cliente",
        "data",
        "total",
        "confirmada",
        "cancelada",
    ]

    list_filter = [
        "confirmada",
        "cancelada",
        "data",
    ]

    search_fields = [
        "=id",
        "cliente__nome",
    ]

    list_select_related = [
        "cliente",
        "cancelada_por",
    ]

    ordering = [
        "-data",
        "-id",
    ]

    date_hierarchy = "data"

    readonly_fields = [
        "data",
        "confirmada",
        "cancelada",
        "motivo_cancelamento",
        "data_cancelamento",
        "cancelada_por",
        "total",
    ]

    inlines = [
        ItemVendaInline,
    ]

    actions = [
        "confirmar_vendas",
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("itens")
        )

    @admin.display(description="Total")
    def total(self, obj):
        if obj is None or obj.pk is None:
            return "R$ 0,00"

        valor = sum(
            (
                item.quantidade * item.preco_unitario
                for item in obj.itens.all()
            ),
            Decimal("0.00"),
        )

        return (
            "R$ "
            + number_format(
                valor,
                decimal_pos=2,
                use_l10n=True,
                force_grouping=True,
            )
        )

    def has_change_permission(self, request, obj=None):
        if obj and (obj.confirmada or obj.cancelada):
            return False

        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Bloqueia a exclusão em lote e permite excluir
        # individualmente apenas vendas não confirmadas.
        if obj is None:
            return False

        if obj.confirmada or obj.cancelada:
            return False

        return super().has_delete_permission(request, obj)

    @admin.action(description="Confirmar vendas selecionadas")
    def confirmar_vendas(self, request, queryset):
        confirmadas = 0

        for venda in queryset.order_by("pk"):
            try:
                confirmar_venda_com_estoque(
                    venda_id=venda.pk,
                    usuario=request.user,
                )
            except ValueError as erro:
                self.message_user(
                    request,
                    f"Venda {venda.pk}: {erro}",
                    level=messages.WARNING,
                )
            else:
                confirmadas += 1

        if confirmadas:
            self.message_user(
                request,
                f"{confirmadas} venda(s) confirmada(s). "
                "Estoque atualizado e histórico registrado.",
                level=messages.SUCCESS,
            )


@admin.register(MovimentoCaixa)
class MovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = [
        "descricao",
        "tipo",
        "valor",
        "data",
        "venda",
    ]

    list_filter = [
        "tipo",
        "data",
    ]

    search_fields = [
        "descricao",
        "=venda__id",
    ]

    list_select_related = [
        "venda",
    ]

    date_hierarchy = "data"

    ordering = [
        "-data",
        "-id",
    ]
    readonly_fields = [
        "descricao",
        "tipo",
        "valor",
        "data",
        "venda",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(EntradaEstoque)
class EntradaEstoqueAdmin(admin.ModelAdmin):
    list_display = [
        "data",
        "produto",
        "quantidade",
        "motivo",
        "usuario",
    ]

    list_filter = [
        "data",
        "produto",
    ]

    search_fields = [
        "produto__nome",
        "produto__codigo",
        "motivo",
        "usuario__username",
    ]

    list_select_related = [
        "produto",
        "usuario",
    ]

    date_hierarchy = "data"

    ordering = [
        "-data",
        "-id",
    ]

    readonly_fields = [
        "produto",
        "quantidade",
        "motivo",
        "data",
        "usuario",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = [
        "data",
        "produto",
        "tipo",
        "origem",
        "quantidade",
        "saldo_apos",
        "venda",
        "usuario",
    ]

    list_filter = [
        "tipo",
        "origem",
        "produto",
        "data",
    ]

    search_fields = [
        "produto__nome",
        "produto__codigo",
        "motivo",
        "=venda__id",
    ]

    list_select_related = [
        "produto",
        "venda",
        "usuario",
    ]

    date_hierarchy = "data"

    ordering = [
        "-data",
        "-id",
    ]

    readonly_fields = [
        "produto",
        "tipo",
        "origem",
        "quantidade",
        "saldo_apos",
        "motivo",
        "data",
        "venda",
        "usuario",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False