from decimal import Decimal

from django import forms

from .models import Produto, Cliente


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