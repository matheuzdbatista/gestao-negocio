from decimal import Decimal

from django.contrib import admin, messages
from django.db import transaction
from django.db.models import F

from .models import (
    Produto,
    Cliente,
    Venda,
    ItemVenda,
    MovimentoCaixa,
)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo", "preco", "estoque")
    search_fields = ("nome", "codigo")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "email")
    search_fields = ("nome", "telefone", "email")


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 1
    min_num = 1
    validate_min = True

    def has_add_permission(self, request, obj=None):
        return not (obj and obj.confirmada)

    def has_change_permission(self, request, obj=None):
        return not (obj and obj.confirmada)

    def has_delete_permission(self, request, obj=None):
        return not (obj and obj.confirmada)


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "data",
        "total",
        "confirmada",
    )
    list_filter = ("confirmada", "data")
    search_fields = ("cliente__nome",)
    inlines = [ItemVendaInline]
    actions = ["confirmar_vendas"]

    @admin.display(description="Total (R$)")
    def total(self, obj):
        valor = sum(
            (
                item.quantidade * item.preco_unitario
                for item in obj.itens.all()
            ),
            Decimal("0.00"),
        )

        return f"{valor:.2f}".replace(".", ",")

    def has_change_permission(self, request, obj=None):
        if obj and obj.confirmada:
            return False

        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is None or obj.confirmada:
            return False

        return super().has_delete_permission(request, obj)

    @admin.action(
        description="Confirmar vendas e baixar estoque",
        permissions=["change"],
    )
    def confirmar_vendas(self, request, queryset):
        for venda_id in queryset.values_list("pk", flat=True):
            try:
                with transaction.atomic():
                    alteradas = Venda.objects.filter(
                        pk=venda_id,
                        confirmada=False,
                    ).update(confirmada=True)

                    if not alteradas:
                        self.message_user(
                            request,
                            f"Venda {venda_id} já estava confirmada.",
                            level=messages.WARNING,
                        )
                        continue

                    itens = list(
                        ItemVenda.objects.filter(venda_id=venda_id)
                    )

                    if not itens:
                        raise ValueError(
                            "A venda não tem produtos."
                        )

                    quantidades = {}

                    for item in itens:
                        if (
                            item.quantidade < 1
                            or item.preco_unitario <= 0
                        ):
                            raise ValueError(
                                "Quantidade e preço devem ser positivos."
                            )

                        quantidades[item.produto_id] = (
                            quantidades.get(item.produto_id, 0)
                            + item.quantidade
                        )

                    for produto_id, quantidade in sorted(
                        quantidades.items()
                    ):
                        atualizados = Produto.objects.filter(
                            pk=produto_id,
                            estoque__gte=quantidade,
                        ).update(
                            estoque=F("estoque") - quantidade
                        )

                        if not atualizados:
                            produto = Produto.objects.get(
                                pk=produto_id
                            )

                            raise ValueError(
                                "Estoque insuficiente para "
                                f"{produto.nome}."
                            )

            except ValueError as erro:
                self.message_user(
                    request,
                    f"Venda {venda_id} não confirmada: {erro}",
                    level=messages.ERROR,
                )

            else:
                self.message_user(
                    request,
                    f"Venda {venda_id} confirmada. Estoque atualizado.",
                    level=messages.SUCCESS,
                )


@admin.register(MovimentoCaixa)
class MovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = ("descricao", "tipo", "valor", "data")
    list_filter = ("tipo", "data")
    search_fields = ("descricao",)
    date_hierarchy = "data"