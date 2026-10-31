from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from .models import (
    Cliente,
    EntradaEstoque,
    ItemVenda,
    MovimentoCaixa,
    Produto,
    Venda,
)


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto

        fields = [
            "nome",
            "codigo",
            "preco",
            "estoque",
            "estoque_minimo",
        ]

        labels = {
            "nome": "Nome",
            "codigo": "Código",
            "preco": "Preço",
            "estoque": "Estoque inicial",
            "estoque_minimo": "Estoque mínimo",
        }

        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Caderno",
                }
            ),
            "codigo": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: CAD001",
                }
            ),
            "preco": forms.NumberInput(
                attrs={
                    "min": "0.01",
                    "step": "0.01",
                }
            ),
            "estoque": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "1",
                }
            ),
            "estoque_minimo": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "1",
                }
            ),
        }

    def clean_preco(self):
        preco = self.cleaned_data["preco"]

        if preco < Decimal("0.01"):
            raise forms.ValidationError(
                "O preço deve ser maior que zero."
            )

        return preco


class ProdutoEdicaoForm(ProdutoForm):
    class Meta(ProdutoForm.Meta):
        fields = [
            "nome",
            "codigo",
            "preco",
            "estoque_minimo",
        ]


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente

        fields = [
            "nome",
            "telefone",
            "email",
        ]

        labels = {
            "nome": "Nome",
            "telefone": "Telefone",
            "email": "E-mail",
        }

        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Matheus",
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: (11) 99999-9999",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Ex.: cliente@example.com",
                }
            ),
        }


class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda

        fields = [
            "cliente",
        ]

        labels = {
            "cliente": "Cliente",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["cliente"].required = False
        self.fields["cliente"].empty_label = "Não informado"
        self.fields["cliente"].queryset = (
            Cliente.objects.order_by("nome", "id")
        )


ItemVendaFormSet = inlineformset_factory(
    Venda,
    ItemVenda,
    fields=[
        "produto",
        "quantidade",
        "preco_unitario",
    ],
    labels={
        "produto": "Produto",
        "quantidade": "Quantidade",
        "preco_unitario": "Preço unitário",
    },
    widgets={
        "quantidade": forms.NumberInput(
            attrs={
                "min": "1",
                "step": "1",
            }
        ),
        "preco_unitario": forms.NumberInput(
            attrs={
                "min": "0.01",
                "step": "0.01",
            }
        ),
    },
    extra=0,
    min_num=1,
    validate_min=True,
    max_num=20,
    validate_max=True,
    can_delete=True,
)


class MovimentoCaixaForm(forms.ModelForm):
    class Meta:
        model = MovimentoCaixa

        fields = [
            "descricao",
            "tipo",
            "valor",
            "data",
        ]

        labels = {
            "descricao": "Descrição",
            "tipo": "Tipo",
            "valor": "Valor",
            "data": "Data do movimento",
        }

        widgets = {
            "descricao": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Compra de embalagem",
                }
            ),
            "valor": forms.NumberInput(
                attrs={
                    "min": "0.01",
                    "step": "0.01",
                }
            ),
            "data": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                },
            ),
        }


class EntradaEstoqueForm(forms.ModelForm):
    class Meta:
        model = EntradaEstoque

        fields = [
            "produto",
            "quantidade",
            "motivo",
        ]

        labels = {
            "produto": "Produto",
            "quantidade": "Quantidade recebida",
            "motivo": "Motivo",
        }

        widgets = {
            "quantidade": forms.NumberInput(
                attrs={
                    "min": "1",
                    "step": "1",
                }
            ),
            "motivo": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Reposição de mercadoria",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["produto"].empty_label = "Selecione um produto"
        self.fields["produto"].queryset = (
            Produto.objects.order_by("nome", "id")
        )


class CancelamentoVendaForm(forms.Form):
    motivo = forms.CharField(
        label="Motivo do cancelamento",
        max_length=200,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Explique por que a venda será cancelada",
            }
        ),
    )


class RecebimentoVendaForm(forms.Form):
    valor = forms.DecimalField(
        label="Valor recebido",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(
            attrs={
                "min": "0.01",
                "step": "0.01",
                "placeholder": "Ex.: 16,00",
            }
        ),
    )

    data = forms.DateField(
        label="Data do recebimento",
        input_formats=[
            "%Y-%m-%d",
            "%d/%m/%Y",
        ],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
            },
        ),
    )


class ReembolsoVendaForm(forms.Form):
    valor = forms.DecimalField(
        label="Valor a devolver",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(
            attrs={
                "min": "0.01",
                "step": "0.01",
                "placeholder": "Ex.: 16,00",
            }
        ),
    )

    data = forms.DateField(
        label="Data do reembolso",
        input_formats=[
            "%Y-%m-%d",
            "%d/%m/%Y",
        ],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
            },
        ),
    )

    motivo = forms.CharField(
        label="Motivo do reembolso",
        max_length=100,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": (
                    "Explique o motivo da devolução do dinheiro"
                ),
            }
        ),
    )
class AjusteEstoqueForm(forms.Form):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.all(),
        label="Produto",
        empty_label="Selecione um produto",
    )

    tipo = forms.ChoiceField(
        label="Tipo de ajuste",
        choices=[
            ("saida", "Saída — perda ou avaria"),
            ("entrada", "Entrada — correção de contagem"),
        ],
    )

    quantidade = forms.IntegerField(
        label="Quantidade do ajuste",
        min_value=1,
        max_value=2147483647,
        widget=forms.NumberInput(
            attrs={
                "min": "1",
                "step": "1",
            }
        ),
    )

    motivo = forms.CharField(
        label="Motivo do ajuste",
        max_length=200,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": (
                    "Ex.: 2 unidades danificadas "
                    "durante o armazenamento"
                ),
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["produto"].queryset = (
            Produto.objects.order_by("nome", "id")
        )