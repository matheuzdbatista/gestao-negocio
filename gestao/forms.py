from decimal import Decimal

from django import forms

from .models import Produto, Cliente

from django.forms import inlineformset_factory

from .models import Venda, ItemVenda

from .models import MovimentoCaixa

from .models import EntradaEstoque


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
            "preco": "Preço (R$)",
            "estoque": "Estoque inicial",
            "estoque_minimo": "Estoque mínimo",
        }
        widgets = {
            "preco": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01"}
            ),
            "estoque": forms.NumberInput(
                attrs={"min": "0"}
            ),
            "estoque_minimo": forms.NumberInput(
                attrs={"min": "0"}
            ),
        }

    def clean_preco(self):
        preco = self.cleaned_data["preco"]

        if preco < Decimal("0.01"):
            raise forms.ValidationError(
                "Informe um preço maior que zero."
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
            "telefone": forms.TextInput(
                attrs={"placeholder": "Ex.: (11) 99999-9999"}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "Ex.: cliente@example.com"}
            ),
        }
class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = ["cliente"]
        labels = {
            "cliente": "Cliente (opcional)",
        }


ItemVendaFormSet = inlineformset_factory(
    Venda,
    ItemVenda,
    fields=["produto", "quantidade", "preco_unitario"],
    labels={
        "produto": "Produto",
        "quantidade": "Quantidade",
        "preco_unitario": "Preço unitário (R$)",
    },
    widgets={
        "quantidade": forms.NumberInput(
            attrs={"min": "1"}
        ),
        "preco_unitario": forms.NumberInput(
            attrs={"min": "0.01", "step": "0.01"}
        ),
    },
    extra=2,
    min_num=1,
    validate_min=True,
    max_num=20,
    validate_max=True,
    can_delete=False,
)
class MovimentoCaixaForm(forms.ModelForm):
    class Meta:
        model = MovimentoCaixa
        fields = ["descricao", "tipo", "valor", "data"]
        labels = {
            "descricao": "Descrição",
            "tipo": "Tipo",
            "valor": "Valor (R$)",
            "data": "Data do movimento",
        }
        widgets = {
            "valor": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01"}
            ),
            "data": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
        }
class EntradaEstoqueForm(forms.ModelForm):
    class Meta:
        model = EntradaEstoque
        fields = ["produto", "quantidade", "motivo"]
        labels = {
            "produto": "Produto",
            "quantidade": "Quantidade recebida",
            "motivo": "Motivo",
        }
        widgets = {
            "quantidade": forms.NumberInput(
                attrs={"min": "1"}
            ),
            "motivo": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Reposição de mercadoria"
                }
            ),
        }