from datetime import date
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F
from django.shortcuts import render

from .models import Cliente, Produto, Venda, ItemVenda, MovimentoCaixa


@staff_member_required
def dashboard(request):
    inicio_texto = request.GET.get("inicio", "")
    fim_texto = request.GET.get("fim", "")

    inicio = None
    fim = None
    erro = ""

    try:
        if inicio_texto:
            inicio = date.fromisoformat(inicio_texto)

        if fim_texto:
            fim = date.fromisoformat(fim_texto)

        if inicio and fim and inicio > fim:
            erro = "A data inicial deve ser anterior ou igual à final."

    except ValueError:
        erro = "Informe datas válidas."

    vendas = Venda.objects.filter(confirmada=True)
    movimentos = MovimentoCaixa.objects.all()

    if not erro:
        if inicio:
            vendas = vendas.filter(data__date__gte=inicio)
            movimentos = movimentos.filter(data__gte=inicio)

        if fim:
            vendas = vendas.filter(data__date__lte=fim)
            movimentos = movimentos.filter(data__lte=fim)
    else:
        vendas = vendas.none()
        movimentos = movimentos.none()

    itens = ItemVenda.objects.filter(venda__in=vendas)

    faturamento = sum(
        (
            item.quantidade * item.preco_unitario
            for item in itens
        ),
        Decimal("0.00"),
    )

    entradas = sum(
        movimentos.filter(tipo="entrada").values_list("valor", flat=True),
        Decimal("0.00"),
    )

    saidas = sum(
        movimentos.filter(tipo="saida").values_list("valor", flat=True),
        Decimal("0.00"),
    )

    estoque_baixo = Produto.objects.filter(
        estoque__lte=F("estoque_minimo")
    ).order_by("estoque", "nome")

    if erro:
        periodo = "Período inválido — corrija as datas"
    elif inicio and fim:
        periodo = (
            f"De {inicio.strftime('%d/%m/%Y')} "
            f"até {fim.strftime('%d/%m/%Y')}"
        )
    elif inicio:
        periodo = f"A partir de {inicio.strftime('%d/%m/%Y')}"
    elif fim:
        periodo = f"Até {fim.strftime('%d/%m/%Y')}"
    else:
        periodo = "Todo o período"

    contexto = {
        "total_produtos": Produto.objects.count(),
        "total_clientes": Cliente.objects.count(),
        "total_vendas": vendas.count(),
        "faturamento": faturamento,
        "estoque_baixo": estoque_baixo,
        "entradas": entradas,
        "saidas": saidas,
        "saldo": entradas - saidas,
        "inicio": inicio_texto,
        "fim": fim_texto,
        "periodo": periodo,
        "erro": erro,
    }

    return render(request, "gestao/dashboard.html", contexto)