from django.db import migrations


def registrar_saldos_iniciais(apps, schema_editor):
    Produto = apps.get_model("gestao", "Produto")
    MovimentoEstoque = apps.get_model(
        "gestao",
        "MovimentoEstoque",
    )

    banco = schema_editor.connection.alias

    produtos = Produto.objects.using(banco).order_by("pk")

    for produto in produtos.iterator():
        # Produtos sem estoque começam com saldo zero,
        # sem necessidade de criar uma entrada.
        if produto.estoque == 0:
            continue

        possui_historico = (
            MovimentoEstoque.objects.using(banco)
            .filter(produto_id=produto.pk)
            .exists()
        )

        if possui_historico:
            continue

        MovimentoEstoque.objects.using(banco).create(
            produto_id=produto.pk,
            tipo="entrada",
            origem="inicial",
            quantidade=produto.estoque,
            saldo_apos=produto.estoque,
            motivo=(
                "Estoque existente no início do histórico "
                "de movimentações."
            ),
        )


class Migration(migrations.Migration):
    dependencies = [
        ("gestao", "0009_movimentoestoque"),
    ]

    operations = [
        migrations.RunPython(
            registrar_saldos_iniciais,
        ),
    ]