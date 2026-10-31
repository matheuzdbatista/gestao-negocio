from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ProdutoForm,
    ProdutoEdicaoForm,
    ClienteForm,
    VendaForm,
    ItemVendaFormSet,
    MovimentoCaixaForm,
    EntradaEstoqueForm,
    CancelamentoVendaForm,
)
from .models import (
    Cliente,
    Produto,
    Venda,
    ItemVenda,
    MovimentoCaixa,
    EntradaEstoque,
)
from .services import cancelar_venda_com_estoque


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

    vendas = Venda.objects.filter(
        confirmada=True,
        cancelada=False,
    )

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
        movimentos.filter(
            tipo="entrada"
        ).values_list("valor", flat=True),
        Decimal("0.00"),
    )

    saidas = sum(
        movimentos.filter(
            tipo="saida"
        ).values_list("valor", flat=True),
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

    return render(
        request,
        "gestao/dashboard.html",
        contexto,
    )


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
        form = ProdutoEdicaoForm(
            request.POST,
            instance=produto,
        )

        if form.is_valid():
            produto_editado = form.save(commit=False)

            # Atualiza somente os campos do formulário.
            # Preserva o estoque mesmo se ele mudar durante a edição.
            produto_editado.save(
                update_fields=[
                    "nome",
                    "codigo",
                    "preco",
                    "estoque_minimo",
                ]
            )

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
        form = ClienteForm(
            request.POST,
            instance=cliente,
        )

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
        .select_related("cliente", "cancelada_por")
        .prefetch_related("itens")
        .order_by("-data", "-id")
    )

    if busca:
        filtro = Q(cliente__nome__icontains=busca)

        if busca.isascii() and busca.isdecimal():
            numero = busca.lstrip("0") or "0"

            if len(numero) <= 19:
                numero_venda = int(numero)

                if numero_venda <= 9223372036854775807:
                    filtro |= Q(pk=numero_venda)

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
        form = VendaForm(
            request.POST,
            instance=venda,
        )

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
                cancelada=False,
            ).update(confirmada=True)

            if not alteradas:
                venda = Venda.objects.get(pk=pk)

                if venda.cancelada:
                    aviso = (
                        f"Venda {pk} cancelada. "
                        "Não é possível confirmá-la novamente."
                    )
                else:
                    aviso = f"Venda {pk} já estava confirmada."

                messages.warning(request, aviso)
                return redirect("lista_vendas")

            itens = list(
                ItemVenda.objects.filter(venda_id=pk)
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


@staff_member_required
def cancelar_venda(request, pk):
    venda = get_object_or_404(Venda, pk=pk)

    if venda.cancelada or not venda.confirmada:
        messages.warning(
            request,
            "A venda já foi cancelada ou não está confirmada.",
        )
        return redirect("lista_vendas")

    if request.method == "POST":
        form = CancelamentoVendaForm(request.POST)

        if form.is_valid():
            try:
                cancelar_venda_com_estoque(
                    venda_id=venda.pk,
                    usuario=request.user,
                    motivo=form.cleaned_data["motivo"],
                )

            except ValueError as erro:
                form.add_error(None, str(erro))

            else:
                messages.success(
                    request,
                    f"Venda {pk} cancelada. "
                    "Produtos devolvidos ao estoque.",
                )

                return redirect("lista_vendas")

    else:
        form = CancelamentoVendaForm()

    return render(
        request,
        "gestao/venda_cancelar.html",
        {
            "venda": venda,
            "form": form,
        },
    )


@staff_member_required
def lista_caixa(request):
    busca = request.GET.get("busca", "").strip()
    tipo = request.GET.get("tipo", "")

    if tipo not in ("entrada", "saida"):
        tipo = ""

    movimentos = (
        MovimentoCaixa.objects
        .all()
        .order_by("-data", "-id")
    )

    if busca:
        movimentos = movimentos.filter(
            descricao__icontains=busca
        )

    if tipo:
        movimentos = movimentos.filter(tipo=tipo)

    entradas = sum(
        movimentos.filter(
            tipo="entrada"
        ).values_list("valor", flat=True),
        Decimal("0.00"),
    )

    saidas = sum(
        movimentos.filter(
            tipo="saida"
        ).values_list("valor", flat=True),
        Decimal("0.00"),
    )

    return render(
        request,
        "gestao/caixa.html",
        {
            "movimentos": movimentos,
            "busca": busca,
            "tipo": tipo,
            "entradas": entradas,
            "saidas": saidas,
            "saldo": entradas - saidas,
        },
    )


@staff_member_required
def novo_movimento(request):
    if request.method == "POST":
        form = MovimentoCaixaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("lista_caixa")

    else:
        form = MovimentoCaixaForm(
            initial={"data": timezone.localdate()}
        )

    return render(
        request,
        "gestao/caixa_form.html",
        {"form": form},
    )


@staff_member_required
def entradas_estoque(request):
    if request.method == "POST":
        form = EntradaEstoqueForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                entrada = form.save(commit=False)
                entrada.usuario = request.user

                Produto.objects.filter(
                    pk=entrada.produto_id
                ).update(
                    estoque=F("estoque") + entrada.quantidade
                )

                entrada.save()

            messages.success(
                request,
                "Entrada registrada e estoque atualizado.",
            )

            return redirect("entradas_estoque")

    else:
        form = EntradaEstoqueForm()

    entradas = (
        EntradaEstoque.objects
        .select_related("produto", "usuario")
        .order_by("-data", "-id")[:50]
    )

    return render(
        request,
        "gestao/entradas_estoque.html",
        {
            "form": form,
            "entradas": entradas,
        },
    )