from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import (
    ItemVenda,
    MovimentoCaixa,
    MovimentoEstoque,
    Produto,
    Venda,
)


def confirmar_venda_com_estoque(venda_id, usuario):
    with transaction.atomic():
        alteradas = Venda.objects.filter(
            pk=venda_id,
            confirmada=False,
            cancelada=False,
        ).update(confirmada=True)

        if not alteradas:
            raise ValueError(
                "A venda já está confirmada, foi cancelada "
                "ou não foi encontrada."
            )

        itens = list(
            ItemVenda.objects.filter(venda_id=venda_id)
        )

        if not itens:
            raise ValueError(
                "Não é possível confirmar uma venda sem itens."
            )

        quantidades = {}

        for item in itens:
            if item.quantidade < 1:
                raise ValueError(
                    "Todos os itens devem ter quantidade "
                    "maior que zero."
                )

            if item.preco_unitario <= Decimal("0.00"):
                raise ValueError(
                    "Todos os itens devem ter preço "
                    "maior que zero."
                )

            quantidades[item.produto_id] = (
                quantidades.get(item.produto_id, 0)
                + item.quantidade
            )

        for produto_id, quantidade in sorted(
            quantidades.items()
        ):
            alterados = Produto.objects.filter(
                pk=produto_id,
                estoque__gte=quantidade,
            ).update(
                estoque=F("estoque") - quantidade,
            )

            if not alterados:
                produto = Produto.objects.filter(
                    pk=produto_id,
                ).first()

                nome = (
                    produto.nome
                    if produto
                    else f"Produto {produto_id}"
                )

                raise ValueError(
                    f"Estoque insuficiente para {nome}."
                )

            produto = Produto.objects.get(pk=produto_id)

            MovimentoEstoque.objects.create(
                produto=produto,
                tipo="saida",
                origem="venda",
                quantidade=quantidade,
                saldo_apos=produto.estoque,
                motivo=f"Confirmação da venda {venda_id}.",
                venda_id=venda_id,
                usuario=usuario,
            )


def cancelar_venda_com_estoque(venda_id, usuario, motivo):
    motivo = motivo.strip()

    if not motivo:
        raise ValueError(
            "Informe o motivo do cancelamento."
        )

    if len(motivo) > 200:
        raise ValueError(
            "O motivo deve ter até 200 caracteres."
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
            raise ValueError(
                "A venda já foi cancelada, não está confirmada "
                "ou não foi encontrada."
            )

        itens = list(
            ItemVenda.objects.filter(venda_id=venda_id)
        )

        if not itens:
            raise ValueError(
                "Esta venda não possui itens."
            )

        quantidades = {}

        for item in itens:
            if item.quantidade < 1:
                raise ValueError(
                    "Esta venda possui quantidade inválida."
                )

            quantidades[item.produto_id] = (
                quantidades.get(item.produto_id, 0)
                + item.quantidade
            )

        for produto_id, quantidade in sorted(
            quantidades.items()
        ):
            alterados = Produto.objects.filter(
                pk=produto_id,
            ).update(
                estoque=F("estoque") + quantidade,
            )

            if not alterados:
                raise ValueError(
                    "Um produto da venda não foi encontrado."
                )

            produto = Produto.objects.get(pk=produto_id)

            MovimentoEstoque.objects.create(
                produto=produto,
                tipo="entrada",
                origem="cancelamento",
                quantidade=quantidade,
                saldo_apos=produto.estoque,
                motivo=motivo,
                venda_id=venda_id,
                usuario=usuario,
            )


def registrar_recebimento_venda(venda_id, valor, data):
    if not isinstance(valor, Decimal):
        raise ValueError(
            "Informe um valor monetário válido."
        )

    if not valor.is_finite() or valor <= Decimal("0.00"):
        raise ValueError(
            "O valor recebido deve ser maior que zero."
        )

    if valor > Decimal("99999999.99"):
        raise ValueError(
            "O valor informado ultrapassa o limite permitido."
        )

    if valor != valor.quantize(Decimal("0.01")):
        raise ValueError(
            "Informe um valor com até duas casas decimais."
        )

    with transaction.atomic():
        # A atualização serializa as operações desta venda.
        alteradas = Venda.objects.filter(
            pk=venda_id,
            confirmada=True,
            cancelada=False,
        ).update(confirmada=True)

        if not alteradas:
            raise ValueError(
                "Só é possível receber pagamentos de vendas "
                "confirmadas e não canceladas."
            )

        itens = list(
            ItemVenda.objects.filter(venda_id=venda_id)
        )

        if not itens:
            raise ValueError(
                "Esta venda não possui itens."
            )

        total = Decimal("0.00")

        for item in itens:
            if (
                item.quantidade < 1
                or item.preco_unitario <= Decimal("0.00")
            ):
                raise ValueError(
                    "Esta venda possui um item com quantidade "
                    "ou preço inválido."
                )

            total += (
                item.quantidade * item.preco_unitario
            )

        recebido = sum(
            MovimentoCaixa.objects.filter(
                venda_id=venda_id,
                tipo="entrada",
            ).values_list("valor", flat=True),
            Decimal("0.00"),
        )

        pendente = total - recebido

        if pendente <= Decimal("0.00"):
            raise ValueError(
                "Esta venda já está totalmente paga."
            )

        if valor > pendente:
            pendente_formatado = (
                f"{pendente:.2f}".replace(".", ",")
            )

            raise ValueError(
                "O recebimento não pode ultrapassar o valor "
                f"pendente de R$ {pendente_formatado}."
            )

        movimento = MovimentoCaixa(
            venda_id=venda_id,
            descricao=f"Recebimento da Venda {venda_id}",
            tipo="entrada",
            valor=valor,
            data=data,
        )

        movimento.full_clean()
        movimento.save()

        return movimento


def registrar_reembolso_venda(
    venda_id,
    valor,
    data,
    motivo,
):
    if not isinstance(valor, Decimal):
        raise ValueError(
            "Informe um valor monetário válido."
        )

    if not valor.is_finite() or valor <= Decimal("0.00"):
        raise ValueError(
            "O valor do reembolso deve ser maior que zero."
        )

    if valor > Decimal("99999999.99"):
        raise ValueError(
            "O valor informado ultrapassa o limite permitido."
        )

    if valor != valor.quantize(Decimal("0.01")):
        raise ValueError(
            "Informe um valor com até duas casas decimais."
        )

    motivo = motivo.strip()

    if not motivo:
        raise ValueError(
            "Informe o motivo do reembolso."
        )

    if len(motivo) > 100:
        raise ValueError(
            "O motivo deve ter até 100 caracteres."
        )

    with transaction.atomic():
        # A atualização serializa os reembolsos desta venda.
        alteradas = Venda.objects.filter(
            pk=venda_id,
            confirmada=True,
            cancelada=True,
        ).update(cancelada=True)

        if not alteradas:
            raise ValueError(
                "Só é possível reembolsar uma venda cancelada."
            )

        recebido = sum(
            MovimentoCaixa.objects.filter(
                venda_id=venda_id,
                tipo="entrada",
            ).values_list("valor", flat=True),
            Decimal("0.00"),
        )

        devolvido = sum(
            MovimentoCaixa.objects.filter(
                venda_id=venda_id,
                tipo="saida",
            ).values_list("valor", flat=True),
            Decimal("0.00"),
        )

        disponivel = recebido - devolvido

        if disponivel <= Decimal("0.00"):
            raise ValueError(
                "Esta venda não possui valor disponível "
                "para reembolso."
            )

        if valor > disponivel:
            disponivel_formatado = (
                f"{disponivel:.2f}".replace(".", ",")
            )

            raise ValueError(
                "O reembolso não pode ultrapassar o valor "
                f"disponível de R$ {disponivel_formatado}."
            )

        movimento = MovimentoCaixa(
            venda_id=venda_id,
            descricao=(
                f"Reembolso da Venda {venda_id}: {motivo}"
            ),
            tipo="saida",
            valor=valor,
            data=data,
        )

        movimento.full_clean()
        movimento.save()

        return movimento