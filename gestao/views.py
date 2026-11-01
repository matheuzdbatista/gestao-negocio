import uuid
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .operacoes import executar_operacao_unica

from .forms import (
    AjusteEstoqueForm,
    CancelamentoVendaForm,
    ClienteForm,
    EntradaEstoqueForm,
    ItemVendaFormSet,
    MovimentoCaixaForm,
    ProdutoEdicaoForm,
    ProdutoForm,
    RecebimentoVendaForm,
    ReembolsoVendaForm,
    VendaForm,
)
from .models import (
    Cliente,
    EntradaEstoque,
    ItemVenda,
    MovimentoCaixa,
    MovimentoEstoque,
    Produto,
    Venda,
)
from .operacoes import executar_operacao_unica
from .services import (
    ajustar_estoque,
    cancelar_venda_com_estoque,
    confirmar_venda_com_estoque,
    registrar_recebimento_venda,
    registrar_reembolso_venda,
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
            with transaction.atomic():
                produto = form.save()

                if produto.estoque > 0:
                    MovimentoEstoque.objects.create(
                        produto=produto,
                        tipo="entrada",
                        origem="inicial",
                        quantidade=produto.estoque,
                        saldo_apos=produto.estoque,
                        motivo="Estoque inicial no cadastro do produto.",
                        usuario=request.user,
                    )

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

        chave_operacao = request.POST.get(
            "chave_operacao", ""
        )

        form_valido = form.is_valid()
        formset_valido = formset.is_valid()

        if form_valido and formset_valido:

            # Inclui os dados do formulário e dos itens.
            # Os valores são serializados de forma consistente.
            dados = {
                "cliente_id": (
                    form.cleaned_data["cliente"].pk
                    if form.cleaned_data["cliente"]
                    else None
                ),
                "itens": [
                    {
                        "produto_id": item["produto"].pk,
                        "quantidade": item["quantidade"],
                        "preco_unitario": str(
                            item["preco_unitario"]
                        ),
                    }
                    for item in formset.cleaned_data
                    if item
                    and not item.get("DELETE", False)
                ],
            }

            def executar():
                venda_salva = form.save()

                formset.instance = venda_salva
                formset.save()

                return reverse(
                    "detalhe_venda",
                    kwargs={"pk": venda_salva.pk},
                )

            try:
                destino, criada = executar_operacao_unica(
                    chave=chave_operacao,
                    usuario=request.user,
                    acao="nova_venda",
                    dados=dados,
                    executar=executar,
                )

            except (ValueError, ValidationError) as erro:
                if isinstance(erro, ValidationError):
                    mensagem = " ".join(erro.messages)
                else:
                    mensagem = str(erro)

                form.add_error(None, mensagem)

            else:
                if criada:
                    messages.success(
                        request,
                        "Venda cadastrada. "
                        "Confirme para baixar o estoque.",
                    )
                else:
                    messages.info(
                        request,
                        "Esta venda já foi cadastrada. "
                        "Nenhuma venda duplicada foi criada.",
                    )

                return redirect(destino)

        # Preserva a chave quando houver erros no formulário.
        try:
            chave_operacao = str(
                uuid.UUID(chave_operacao)
            )
        except (ValueError, TypeError, AttributeError):
            chave_operacao = str(uuid.uuid4())

    else:
        form = VendaForm(instance=venda)

        formset = ItemVendaFormSet(
            instance=venda,
            prefix="itens",
        )

        chave_operacao = str(uuid.uuid4())

    produtos = Produto.objects.order_by("nome", "id")

    precos_produtos = {
        str(produto.pk): str(produto.preco)
        for produto in produtos
    }

    return render(
        request,
        "gestao/venda_form.html",
        {
            "form": form,
            "formset": formset,
            "precos_produtos": precos_produtos,
            "chave_operacao": chave_operacao,
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

    form_recebimento = RecebimentoVendaForm(
        initial={
            "data": timezone.localdate(),
        }
    )

    form_reembolso = ReembolsoVendaForm(
        initial={
            "data": timezone.localdate(),
        }
    )

    chave_recebimento = str(uuid.uuid4())
    chave_reembolso = str(uuid.uuid4())


    if request.method == "POST":
        chave_enviada = request.POST.get("chave_operacao", "")

        try:
            chave_enviada = str(uuid.UUID(chave_enviada))
        except (ValueError, TypeError, AttributeError):
            # deixa a chave inválida para que a operação \/
            # dê rejeite em vez de criar outra automaticamente
            pass

        acao_enviada = request.POST.get("acao", "receber")

        if acao_enviada == "receber":
            chave_recebimento = chave_enviada

        elif acao_enviada == "reembolsar":
            chave_reembolso = chave_enviada

    if request.method == "POST":
        acao = request.POST.get("acao", "receber")

        if acao == "receber":
            form_recebimento = RecebimentoVendaForm(request.POST)

            if form_recebimento.is_valid():
                try:
                    dados = {
                        "venda_id": venda.pk,
                        "valor": str(
                            form_recebimento.cleaned_data["valor"]
                        ),
                        "data": (
                            form_recebimento.cleaned_data["data"].isoformat()
                        ),
                    }

                    def executar_recebimento():
                        registrar_recebimento_venda(
                            venda_id=venda.pk,
                            valor=form_recebimento.cleaned_data["valor"],
                            data=form_recebimento.cleaned_data["data"],
                        )

                        return reverse(
                            "detalhe_venda",
                            kwargs={"pk": venda.pk},
                        )

                    destino, criada = executar_operacao_unica(
                        chave=chave_recebimento,
                        usuario=request.user,
                        acao="recebimento_venda",
                        dados=dados,
                        executar=executar_recebimento,
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
                    if criada:
                        messages.success(
                            request,
                            "Recebimento registrado no caixa com sucesso.",
                        )
                    else:
                        messages.info(
                            request,
                            "Este recebimento já foi registrado. "
                            "Nenhum lançamento duplicado foi criado.",
                        )

                    return redirect(destino)

        elif acao == "reembolsar":
            form_reembolso = ReembolsoVendaForm(request.POST)

            if form_reembolso.is_valid():
                try:
                    dados = {
                        "venda_id": venda.pk,
                        "valor": str(
                            form_reembolso.cleaned_data["valor"]
                        ),
                        "data": (
                            form_reembolso.cleaned_data["data"].isoformat()
                        ),
                        "motivo": form_reembolso.cleaned_data["motivo"],
                    }

                    def executar_reembolso():
                        registrar_reembolso_venda(
                            venda_id=venda.pk,
                            valor=form_reembolso.cleaned_data["valor"],
                            data=form_reembolso.cleaned_data["data"],
                            motivo=form_reembolso.cleaned_data["motivo"],
                        )

                        return reverse(
                            "detalhe_venda",
                            kwargs={"pk": venda.pk},
                        )

                    destino, criada = executar_operacao_unica(
                        chave=chave_reembolso,
                        usuario=request.user,
                        acao="reembolso_venda",
                        dados=dados,
                        executar=executar_reembolso,
                    )
                except ValueError as erro:
                    form_reembolso.add_error(
                        None,
                        str(erro),
                    )
                except ValidationError as erro:
                    form_reembolso.add_error(
                        None,
                        " ".join(erro.messages),
                    )
                else:
                    if criada:
                        messages.success(
                            request,
                            "Reembolso registrado como saída no caixa.",
                        )
                    else:
                        messages.info(
                            request,
                            "Este reembolso já foi registrado. "
                            "Nenhuma saída duplicada foi criada.",
                        )

                    return redirect(destino)

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

    reembolsos = list(
        venda.movimentos_caixa.filter(
            tipo="saida",
        ).order_by("-data", "-id")
    )

    total_recebido = sum(
        (movimento.valor for movimento in recebimentos),
        Decimal("0.00"),
    )

    total_reembolsado = sum(
        (movimento.valor for movimento in reembolsos),
        Decimal("0.00"),
    )

    valor_pendente = max(
        total - total_recebido,
        Decimal("0.00"),
    )

    valor_a_reembolsar = max(
        total_recebido - total_reembolsado,
        Decimal("0.00"),
    )

    pode_receber = (
        venda.confirmada
        and not venda.cancelada
        and valor_pendente > Decimal("0.00")
    )

    pode_reembolsar = (
        venda.confirmada
        and venda.cancelada
        and valor_a_reembolsar > Decimal("0.00")
    )

    return render(
        request,
        "gestao/venda_detalhe.html",
        {
            "chave_recebimento": chave_recebimento,
            "chave_reembolso": chave_reembolso,
            "venda": venda,
            "itens": itens,
            "total": total,
            "recebimentos": recebimentos,
            "total_recebido": total_recebido,
            "valor_pendente": valor_pendente,
            "pode_receber": pode_receber,
            "form_recebimento": form_recebimento,
            "reembolsos": reembolsos,
            "total_reembolsado": total_reembolsado,
            "valor_a_reembolsar": valor_a_reembolsar,
            "pode_reembolsar": pode_reembolsar,
            "form_reembolso": form_reembolso,
        },
    )

@staff_member_required
@require_POST
def confirmar_venda(request, pk):
    get_object_or_404(Venda, pk=pk)

    try:
        confirmar_venda_com_estoque(
            venda_id=pk,
            usuario=request.user,
        )
    except ValueError as erro:
        messages.error(
            request,
            str(erro),
        )
    else:
        messages.success(
            request,
            f"Venda {pk} confirmada. "
            "Estoque atualizado e histórico registrado.",
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

        chave_operacao = request.POST.get(
            "chave_operacao", ""
        )

        if form.is_valid():
            dados = {
                "produto_id": form.cleaned_data["produto"].pk,
                "quantidade": form.cleaned_data["quantidade"],
                "motivo": form.cleaned_data["motivo"],
            }

            def executar():
                entrada = form.save(commit=False)
                entrada.usuario = request.user

                alterados = Produto.objects.filter(
                    pk=entrada.produto_id,
                    estoque__lte=2147483647 - entrada.quantidade,
                ).update(
                    estoque=F("estoque") + entrada.quantidade,
                )

                if not alterados:
                    raise ValueError(
                        "Produto não encontrado ou "
                        "limite de estoque excedido."
                    )

                produto = Produto.objects.get(
                    pk=entrada.produto_id,
                )

                entrada.save()

                movimento = MovimentoEstoque(
                    produto=produto,
                    tipo="entrada",
                    origem="reposicao",
                    quantidade=entrada.quantidade,
                    saldo_apos=produto.estoque,
                    motivo=entrada.motivo,
                    usuario=request.user,
                )

                movimento.full_clean()
                movimento.save()

                return reverse("entradas_estoque")

            try:
                destino, criada = executar_operacao_unica(
                    chave=chave_operacao,
                    usuario=request.user,
                    acao="entrada_estoque",
                    dados=dados,
                    executar=executar,
                )

            except (ValueError, ValidationError) as erro:
                if isinstance(erro, ValidationError):
                    mensagem = " ".join(erro.messages)
                else:
                    mensagem = str(erro)

                form.add_error(None, mensagem)

            else:
                if criada:
                    messages.success(
                        request,
                        "Entrada registrada e estoque atualizado.",
                    )
                else:
                    messages.info(
                        request,
                        "Esta entrada já foi processada. "
                        "O estoque não foi alterado novamente.",
                    )

                return redirect(destino)

        try:
            chave_operacao = str(uuid.UUID(chave_operacao))
        except (ValueError, TypeError, AttributeError):
            chave_operacao = str(uuid.uuid4())

    else:
        form = EntradaEstoqueForm()
        chave_operacao = str(uuid.uuid4())

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
            "chave_operacao": chave_operacao,
        },
)
@staff_member_required
def historico_estoque(request):
    busca = request.GET.get("busca", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    origem = request.GET.get("origem", "").strip()
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()

    tipos_validos = dict(MovimentoEstoque.TIPOS)
    origens_validas = dict(MovimentoEstoque.ORIGENS)

    if tipo not in tipos_validos:
        tipo = ""

    if origem not in origens_validas:
        origem = ""

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

    movimentos = (
        MovimentoEstoque.objects.select_related(
            "produto",
            "venda",
            "usuario",
        )
        .order_by("-data", "-id")
    )

    if busca:
        movimentos = movimentos.filter(
            Q(produto__nome__icontains=busca)
            | Q(produto__codigo__icontains=busca)
        )

    if tipo:
        movimentos = movimentos.filter(tipo=tipo)

    if origem:
        movimentos = movimentos.filter(origem=origem)

    if erro:
        movimentos = movimentos.none()
    else:
        if data_inicio:
            movimentos = movimentos.filter(
                data__date__gte=data_inicio,
            )

        if data_fim:
            movimentos = movimentos.filter(
                data__date__lte=data_fim,
            )

    paginador = Paginator(movimentos, 25)
    pagina = paginador.get_page(request.GET.get("page"))

    filtros = request.GET.copy()
    filtros.pop("page", None)

    return render(
        request,
        "gestao/historico_estoque.html",
        {
            "movimentos": pagina,
            "pagina": pagina,
            "total_movimentos": paginador.count,
            "busca": busca,
            "tipo": tipo,
            "origem": origem,
            "inicio": inicio,
            "fim": fim,
            "erro": erro,
            "tipos": MovimentoEstoque.TIPOS,
            "origens": MovimentoEstoque.ORIGENS,
            "filtros_url": filtros.urlencode(),
        },
    )


@staff_member_required
def ajuste_estoque(request):
    if request.method == "POST":
        form = AjusteEstoqueForm(request.POST)
        chave_operacao = request.POST.get(
            "chave_operacao",
            "",
        )

        if form.is_valid():
            dados = {
                "produto_id": form.cleaned_data["produto"].pk,
                "tipo": form.cleaned_data["tipo"],
                "quantidade": form.cleaned_data["quantidade"],
                "motivo": form.cleaned_data["motivo"],
            }

            def executar():
                ajustar_estoque(
                    produto_id=dados["produto_id"],
                    tipo=dados["tipo"],
                    quantidade=dados["quantidade"],
                    motivo=dados["motivo"],
                    usuario=request.user,
                )

                return reverse("lista_produtos")

            try:
                destino, criada = executar_operacao_unica(
                    chave=chave_operacao,
                    usuario=request.user,
                    acao="ajuste_estoque",
                    dados=dados,
                    executar=executar,
                )
            except ValueError as erro:
                form.add_error(
                    None,
                    str(erro),
                )
            except ValidationError as erro:
                form.add_error(
                    None,
                    " ".join(erro.messages),
                )
            else:
                if criada:
                    messages.success(
                        request,
                        "Ajuste registrado com sucesso.",
                    )
                else:
                    messages.info(
                        request,
                        "Este ajuste já foi processado. "
                        "Nenhuma alteração foi repetida.",
                    )

                return redirect(destino)

        try:
            chave_operacao = str(
                uuid.UUID(chave_operacao)
            )
        except (ValueError, TypeError, AttributeError):
            chave_operacao = str(uuid.uuid4())
    else:
        form = AjusteEstoqueForm()
        chave_operacao = str(uuid.uuid4())

    return render(
        request,
        "gestao/ajuste_estoque.html",
        {
            "form": form,
            "chave_operacao": chave_operacao,
        },
    )