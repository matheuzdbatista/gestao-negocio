from datetime import date
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from .forms import ProdutoForm, ProdutoEdicaoForm, ClienteForm
from .models import Cliente, Produto, Venda, ItemVenda, MovimentoCaixa
from django.db import transaction

from .forms import VendaForm, ItemVendaFormSet


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


@staff_member_required
def lista_produtos(request):
    busca = request.GET.get("busca", "").strip()
    produtos = Produto.objects.all().order_by("nome", "id")

    if busca:
        produtos = produtos.filter(
            Q(nome__icontains=busca)
            | Q(codigo__icontains=busca)
        )

    return render(
        request,
        "gestao/produtos.html",
        {
            "produtos": produtos,
            "busca": busca,
        },
    )


@staff_member_required
def novo_produto(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("lista_produtos")
    else:
        form = ProdutoForm()

    return render(
        request,
        "gestao/produto_form.html",
        {
            "form": form,
            "editando": False,
        },
    )


@staff_member_required
def editar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)

    if request.method == "POST":
        form = ProdutoEdicaoForm(request.POST, instance=produto)

        if form.is_valid():
            form.save()
            return redirect("lista_produtos")
    else:
        form = ProdutoEdicaoForm(instance=produto)

    return render(
        request,
        "gestao/produto_form.html",
        {
            "form": form,
            "editando": True,
        },
    )


@staff_member_required
def lista_clientes(request):
    busca = request.GET.get("busca", "").strip()
    clientes = Cliente.objects.all().order_by("nome", "id")

    if busca:
        clientes = clientes.filter(
            Q(nome__icontains=busca)
            | Q(telefone__icontains=busca)
            | Q(email__icontains=busca)
        )

    return render(
        request,
        "gestao/clientes.html",
        {
            "clientes": clientes,
            "busca": busca,
        },
    )


@staff_member_required
def novo_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("lista_clientes")
    else:
        form = ClienteForm()

    return render(
        request,
        "gestao/cliente_form.html",
        {
            "form": form,
            "editando": False,
        },
    )


@staff_member_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)

        if form.is_valid():
            form.save()
            return redirect("lista_clientes")
    else:
        form = ClienteForm(instance=cliente)

    return render(
        request,
        "gestao/cliente_form.html",
        {
            "form": form,
            "editando": True,
        },
    )
@staff_member_required
def lista_vendas(request):
    busca = request.GET.get("busca", "").strip()

    vendas = (
        Venda.objects
        .select_related("cliente")
        .prefetch_related("itens")
        .order_by("-data", "-id")
    )

    if busca:
        filtro = Q(cliente__nome__icontains=busca)

        if busca.isdigit():
            filtro |= Q(pk=int(busca))

        vendas = vendas.filter(filtro)

    for venda in vendas:
        venda.total_calculado = sum(
            (
                item.quantidade * item.preco_unitario
                for item in venda.itens.all()
            ),
            Decimal("0.00"),
        )

    return render(
        request,
        "gestao/vendas.html",
        {
            "vendas": vendas,
            "busca": busca,
        },
    )
@staff_member_required
def nova_venda(request):
    venda = Venda()

    if request.method == "POST":
        form = VendaForm(request.POST, instance=venda)

        formset = ItemVendaFormSet(
            request.POST,
            instance=venda,
            prefix="itens",
        )

        form_valido = form.is_valid()
        itens_validos = formset.is_valid()

        if form_valido and itens_validos:
            with transaction.atomic():
                venda = form.save()
                formset.instance = venda
                formset.save()

            return redirect("lista_vendas")

    else:
        form = VendaForm(instance=venda)

        formset = ItemVendaFormSet(
            instance=venda,
            prefix="itens",
        )

    return render(
        request,
        "gestao/venda_form.html",
        {
            "form": form,
            "formset": formset,
        },
    )
@staff_member_required
@require_POST
def confirmar_venda(request, pk):
    get_object_or_404(Venda, pk=pk)

    try:
        with transaction.atomic():
            alteradas = Venda.objects.filter(
                pk=pk,
                confirmada=False,
            ).update(confirmada=True)

            if not alteradas:
                messages.warning(
                    request,
                    f"Venda {pk} já estava confirmada.",
                )
                return redirect("lista_vendas")

            itens = list(
                ItemVenda.objects.filter(venda_id=pk)
            )

            if not itens:
                raise ValueError("A venda não tem produtos.")

            quantidades = {}

            for item in itens:
                if item.quantidade < 1 or item.preco_unitario <= 0:
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
                    produto = Produto.objects.get(pk=produto_id)

                    raise ValueError(
                        f"Estoque insuficiente para {produto.nome}."
                    )

    except ValueError as erro:
        messages.error(
            request,
            f"Venda {pk} não confirmada: {erro}",
        )

    else:
        messages.success(
            request,
            f"Venda {pk} confirmada. Estoque atualizado.",
        )

    return redirect("lista_vendas")