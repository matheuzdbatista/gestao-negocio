from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    CancelamentoVendaForm,
    ClienteForm,
    EntradaEstoqueForm,
    ItemVendaFormSet,
    MovimentoCaixaForm,
    ProdutoEdicaoForm,
    ProdutoForm,
    RecebimentoVendaForm,
    VendaForm,
)
from .models import (
    Cliente,
    EntradaEstoque,
    ItemVenda,
    MovimentoCaixa,
    Produto,
    Venda,
)
from .services import (
    cancelar_venda_com_estoque,
    registrar_recebimento_venda,
)


@staff_member_required
def dashboard(request):
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()

    data_inicio = None
    data_fim = None
    erro = ""

    try:
        if inicio:
            data_inicio = date.fromisoformat(inicio)

        if fim:
            data_fim = date.fromisoformat(fim)
    except ValueError:
        erro = "Informe datas válidas para o período."

    if (
        not erro
        and data_inicio
        and data_fim
        and data_inicio > data_fim
    ):
        erro = "A data inicial não pode ser posterior à data final."

    vendas = Venda.objects.filter(
        confirmada=True,
        cancelada=False,
    )

    movimentos = MovimentoCaixa.objects.all()

    if erro:
        vendas = vendas.none()
        movimentos = movimentos.none()
        periodo = "Período inválido"
    else:
        if data_inicio:
            vendas = vendas.filter(
                data__date__gte=data_inicio,
            )
            movimentos = movimentos.filter(
                data__gte=data_inicio,
            )

        if data_fim:
            vendas = vendas.filter(
                data__date__lte=data_fim,
            )
            movimentos = movimentos.filter(
                data__lte=data_fim,
            )

        if data_inicio and data_fim:
            periodo = (
                f"{data_inicio:%d/%m/%Y} "
                f"a {data_fim:%d/%m/%Y}"
            )
        elif data_inicio:
            periodo = f"A partir de {data_inicio:%d/%m/%Y}"
        elif data_fim:
            periodo = f"Até {data_fim:%d/%m/%Y}"
        else:
            periodo = "Todo o período"

    faturamento = sum(
        (
            item.quantidade * item.preco_unitario
            for item in ItemVenda.objects.filter(
                venda__in=vendas,
            )
        ),
        Decimal("0.00"),
    )

    entradas = sum(
        movimentos.filter(
            tipo="entrada",
        ).values_list("valor", flat=True),
        Decimal("0.00"),
    )

    saidas = sum(
        movimentos.filter(
            tipo="saida",
        ).values_list("valor", flat=True),
        Decimal("0.00"),
    )

    estoque_baixo = Produto.objects.filter(
        estoque__lte=F("estoque_minimo"),
    ).order_by("nome", "id")

    return render(
        request,
        "gestao/dashboard.html",
        {
            "total_produtos": Produto.objects.count(),
            "total_clientes": Cliente.objects.count(),
            "total_vendas": vendas.count(),
            "faturamento": faturamento,
            "estoque_baixo": estoque_baixo,
            "entradas": entradas,
            "saidas": saidas,
            "saldo": entradas - saidas,
            "inicio": inicio,
            "fim": fim,
            "periodo": periodo,
            "erro": erro,
        },
    )


@staff_member_required
def lista_produtos(request):
    busca = request.GET.get("busca", "").strip()

    produtos = Produto.objects.all()

    if busca:
        produtos = produtos.filter(
            Q(nome__icontains=busca)
            | Q(codigo__icontains=busca)
        )

    produtos = produtos.order_by("nome", "id")

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

            messages.success(
                request,
                "Produto cadastrado com sucesso.",
            )

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

            produto_editado.save(
                update_fields=[
                    "nome",
                    "codigo",
                    "preco",
                    "estoque_minimo",
                ]
            )

            messages.success(
                request,
                "Produto atualizado com sucesso.",
            )

            return redirect("lista_produtos")
    else:
        form = ProdutoEdicaoForm(instance=produto)

    return render(
        request,
        "gestao/produto_form.html",
        {
            "form": form,
            "produto": produto,
            "editando": True,
        },
    )


@staff_member_required
def lista_clientes(request):
    busca = request.GET.get("busca", "").strip()

    clientes = Cliente.objects.all()

    if busca:
        clientes = clientes.filter(
            Q(nome__icontains=busca)
            | Q(telefone__icontains=busca)
            | Q(email__icontains=busca)
        )

    clientes = clientes.order_by("nome", "id")

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

            messages.success(
                request,
                "Cliente cadastrado com sucesso.",
            )

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

            messages.success(
                request,
                "Cliente atualizado com sucesso.",
            )

            return redirect("lista_clientes")
    else:
        form = ClienteForm(instance=cliente)

    return render(
        request,
        "gestao/cliente_form.html",
        {
            "form": form,
            "cliente": cliente,
            "editando": True,
        },
    )


@staff_member_required
def lista_vendas(request):
    busca = request.GET.get("busca", "").strip()

    vendas = (
        Venda.objects.select_related(
            "cliente",
            "cancelada_por",
        )
        .prefetch_related("itens")
        .order_by("-data", "-id")
    )

    if busca:
        filtro = Q(cliente__nome__icontains=busca)

        if busca.isascii() and busca.isdecimal():
            numero_texto = busca.lstrip("0") or "0"

            if len(numero_texto) <= 19:
                numero = int(numero_texto)

                if numero <= 9223372036854775807:
                    filtro |= Q(pk=numero)

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
        formset_valido = formset.is_valid()

        if form_valido and formset_valido:
            with transaction.atomic():
                venda = form.save()
                formset.instance = venda
                formset.save()

            messages.success(
                request,
                "Venda cadastrada. Confirme para baixar o estoque.",
            )

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
def detalhe_venda(request, pk):
    venda = get_object_or_404(
        Venda.objects.select_related(
            "cliente",
            "cancelada_por",
        ),
        pk=pk,
    )

    if request.method == "POST":
        form_recebimento = RecebimentoVendaForm(request.POST)

        if form_recebimento.is_valid():
            try:
                registrar_recebimento_venda(
                    venda_id=venda.pk,
                    valor=form_recebimento.cleaned_data["valor"],
                    data=form_recebimento.cleaned_data["data"],
                )
            except ValueError as erro:
                form_recebimento.add_error(
                    None,
                    str(erro),
                )
            except ValidationError as erro:
                form_recebimento.add_error(
                    None,
                    " ".join(erro.messages),
                )
            else:
                messages.success(
                    request,
                    "Recebimento registrado no caixa com sucesso.",
                )

                return redirect(
                    "detalhe_venda",
                    pk=venda.pk,
                )
    else:
        form_recebimento = RecebimentoVendaForm(
            initial={
                "data": timezone.localdate(),
            }
        )

    venda.refresh_from_db()

    itens = list(
        venda.itens.select_related("produto").order_by("id")
    )

    total = Decimal("0.00")

    for item in itens:
        item.subtotal = item.quantidade * item.preco_unitario
        total += item.subtotal

    recebimentos = list(
        venda.movimentos_caixa.filter(
            tipo="entrada",
        ).order_by("-data", "-id")
    )

    total_recebido = sum(
        (movimento.valor for movimento in recebimentos),
        Decimal("0.00"),
    )

    valor_pendente = max(
        total - total_recebido,
        Decimal("0.00"),
    )

    pode_receber = (
        venda.confirmada
        and not venda.cancelada
        and valor_pendente > Decimal("0.00")
    )

    return render(
        request,
        "gestao/venda_detalhe.html",
        {
            "venda": venda,
            "itens": itens,
            "total": total,
            "recebimentos": recebimentos,
            "total_recebido": total_recebido,
            "valor_pendente": valor_pendente,
            "pode_receber": pode_receber,
            "form_recebimento": form_recebimento,
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
                venda_atual = Venda.objects.get(pk=pk)

                if venda_atual.cancelada:
                    messages.warning(
                        request,
                        "Uma venda cancelada não pode ser confirmada.",
                    )
                else:
                    messages.warning(
                        request,
                        "Esta venda já está confirmada.",
                    )

                return redirect("lista_vendas")

            itens = list(
                ItemVenda.objects.filter(venda_id=pk)
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

                    nome_produto = (
                        produto.nome
                        if produto
                        else f"Produto {produto_id}"
                    )

                    raise ValueError(
                        f"Estoque insuficiente para {nome_produto}."
                    )

    except ValueError as erro:
        messages.error(
            request,
            str(erro),
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
                form.add_error(
                    None,
                    str(erro),
                )
            else:
                messages.success(
                    request,
                    f"Venda {venda.pk} cancelada. "
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
    tipo = request.GET.get("tipo", "").strip()

    if tipo not in ("entrada", "saida"):
        tipo = ""

    movimentos = MovimentoCaixa.objects.all()

    if busca:
        movimentos = movimentos.filter(
            descricao__icontains=busca,
        )

    if tipo:
        movimentos = movimentos.filter(tipo=tipo)

    movimentos = movimentos.order_by("-data", "-id")

    entradas = sum(
        movimentos.filter(
            tipo="entrada",
        ).values_list("valor", flat=True),
        Decimal("0.00"),
    )

    saidas = sum(
        movimentos.filter(
            tipo="saida",
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

            messages.success(
                request,
                "Movimento de caixa registrado com sucesso.",
            )

            return redirect("lista_caixa")
    else:
        form = MovimentoCaixaForm(
            initial={
                "data": timezone.localdate(),
            }
        )

    return render(
        request,
        "gestao/caixa_form.html",
        {
            "form": form,
        },
    )


@staff_member_required
def entradas_estoque(request):
    if request.method == "POST":
        form = EntradaEstoqueForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                entrada = form.save(commit=False)
                entrada.usuario = request.user

                alterados = Produto.objects.filter(
                    pk=entrada.produto_id,
                ).update(
                    estoque=F("estoque") + entrada.quantidade,
                )

                if not alterados:
                    raise ValueError(
                        "O produto informado não foi encontrado."
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
        EntradaEstoque.objects.select_related(
            "produto",
            "usuario",
        )
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