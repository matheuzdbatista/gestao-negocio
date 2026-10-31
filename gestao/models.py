from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
import uuid


class Produto(models.Model):
    nome = models.CharField(max_length=100)

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    estoque = models.PositiveIntegerField(default=0)

    estoque_minimo = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.nome


class Cliente(models.Model):
    nome = models.CharField(max_length=100)

    telefone = models.CharField(
        max_length=20,
        blank=True,
    )

    email = models.EmailField(blank=True)

    def __str__(self):
        return self.nome


class Venda(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    data = models.DateTimeField(auto_now_add=True)

    confirmada = models.BooleanField(
        default=False,
        editable=False,
    )

    cancelada = models.BooleanField(
        default=False,
        editable=False,
    )

    motivo_cancelamento = models.CharField(
        max_length=200,
        blank=True,
        editable=False,
    )

    data_cancelamento = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    cancelada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="vendas_canceladas",
    )

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"Venda {self.pk}"


class ItemVenda(models.Model):
    venda = models.ForeignKey(
        Venda,
        on_delete=models.CASCADE,
        related_name="itens",
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
    )

    quantidade = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    preco_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
    )

    def __str__(self):
        return f"{self.quantidade} x {self.produto.nome}"


class MovimentoCaixa(models.Model):
    TIPOS = [
        ("entrada", "Entrada"),
        ("saida", "Saída"),
    ]

    descricao = models.CharField(
        "descrição",
        max_length=150,
    )

    tipo = models.CharField(
        max_length=7,
        choices=TIPOS,
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
    )

    data = models.DateField("data do movimento")

    venda = models.ForeignKey(
        "Venda",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimentos_caixa",
        verbose_name="venda vinculada",
    )

    class Meta:
        verbose_name = "movimento de caixa"
        verbose_name_plural = "movimentos de caixa"
        ordering = ["-data", "-id"]

    def __str__(self):
        return self.descricao


class EntradaEstoque(models.Model):
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="entradas_estoque",
    )

    quantidade = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    motivo = models.CharField(max_length=200)

    data = models.DateTimeField(auto_now_add=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="entradas_estoque",
    )

    class Meta:
        verbose_name = "entrada de estoque"
        verbose_name_plural = "entradas de estoque"
        ordering = ["-data", "-id"]

    def __str__(self):
        return (
            f"{self.produto.nome}: "
            f"+{self.quantidade} unidades"
        )
class MovimentoEstoque(models.Model):
    TIPOS = [
        ("entrada", "Entrada"),
        ("saida", "Saída"),
    ]

    ORIGENS = [
        ("inicial", "Saldo inicial"),
        ("reposicao", "Reposição"),
        ("venda", "Venda confirmada"),
        ("cancelamento", "Cancelamento de venda"),
        ("ajuste", "Ajuste de estoque"),
    ]

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="movimentos_estoque",
    )

    tipo = models.CharField(
        max_length=7,
        choices=TIPOS,
    )

    origem = models.CharField(
        max_length=15,
        choices=ORIGENS,
    )

    quantidade = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    saldo_apos = models.PositiveIntegerField(
        verbose_name="estoque após o movimento",
    )

    motivo = models.CharField(
        max_length=200,
    )

    data = models.DateTimeField(auto_now_add=True)

    venda = models.ForeignKey(
        Venda,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimentos_estoque",
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimentos_estoque",
    )

    class Meta:
        verbose_name = "movimento de estoque"
        verbose_name_plural = "movimentos de estoque"
        ordering = ["-data", "-id"]

    def __str__(self):
        sinal = "+" if self.tipo == "entrada" else "-"

        return (
            f"{self.produto.nome}: "
            f"{sinal}{self.quantidade}"
        )
class OperacaoFormulario(models.Model):
    chave = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="operacoes_formulario",
    )

    acao = models.CharField(
        max_length=50,
    )

    assinatura_dados = models.CharField(
        max_length=64,
    )

    destino = models.CharField(
        max_length=250,
        blank=True,
    )

    criada_em = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "operação de formulário"
        verbose_name_plural = "operações de formulário"
        ordering = ["-criada_em", "-id"]

    def __str__(self):
        return f"{self.acao}: {self.chave}"