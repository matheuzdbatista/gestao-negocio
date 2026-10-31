from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Produto, Venda, ItemVenda


def cancelar_venda_com_estoque(venda_id, usuario, motivo):
    motivo = motivo.strip()

    if not motivo:
        raise ValueError("Informe o motivo do cancelamento.")

    if len(motivo) > 200:
        raise ValueError(
            "O motivo deve ter no máximo 200 caracteres."
        )

    with transaction.atomic():
        alteradas = Venda.objects.filter(
            pk=venda_id,
            confirmada=True,
            cancelada=False,
        ).update(
            cancelada=True,
            motivo_cancelamento=motivo,
            data_cancelamento=timezone.now(),
            cancelada_por=usuario,
        )

        if not alteradas:
            venda = Venda.objects.filter(pk=venda_id).first()

            if venda is None:
                raise ValueError("Venda não encontrada.")

            if venda.cancelada:
                raise ValueError("Esta venda já foi cancelada.")

            raise ValueError(
                "Somente vendas confirmadas podem ser canceladas."
            )

        itens = list(
            ItemVenda.objects.filter(venda_id=venda_id)
        )

        if not itens:
            raise ValueError("A venda não possui produtos.")

        quantidades = {}

        for item in itens:
            if item.quantidade < 1:
                raise ValueError(
                    "A venda possui uma quantidade inválida."
                )

            quantidades[item.produto_id] = (
                quantidades.get(item.produto_id, 0)
                + item.quantidade
            )

        for produto_id, quantidade in sorted(
            quantidades.items()
        ):
            atualizados = Produto.objects.filter(
                pk=produto_id
            ).update(
                estoque=F("estoque") + quantidade
            )

            if not atualizados:
                raise ValueError(
                    "Um produto da venda não foi encontrado."
                )