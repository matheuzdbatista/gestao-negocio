import uuid
from decimal import Decimal

from .services import cancelar_venda_com_estoque
from .models import MovimentoEstoque
from .services import confirmar_venda_com_estoque
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Produto,
    OperacaoFormulario,
    Venda,
    ItemVenda,
    MovimentoCaixa,
)

from .operacoes import executar_operacao_unica

class ProtecaoDuplicidadeTest(TestCase):

    def setUp(self):
        # Cria um usuário para executar as operações
        self.usuario = get_user_model().objects.create_user(
            username="usuario_teste",
            password="SenhaTeste123!",
        )

        # Cria um produto fictício
        self.produto = Produto.objects.create(
            nome="Café",
            codigo="CAF001",
            preco=Decimal("25.00"),
            estoque=10,
            estoque_minimo=3,
        )

    def test_reposicao_nao_pode_ser_duplicada(self):
        # Identificador único da operação
        chave = uuid.uuid4()

        dados = {
            "produto_id": self.produto.pk,
            "quantidade": 10,
            "motivo": "Reposição de teste",
        }

        def executar():
            produto = Produto.objects.get(pk=self.produto.pk)
            produto.estoque += 10
            produto.save(update_fields=["estoque"])

            return "/estoque/entradas/"

        # Primeira solicitação
        destino1, criada1 = executar_operacao_unica(
            chave=chave,
            usuario=self.usuario,
            acao="entrada_estoque",
            dados=dados,
            executar=executar,
        )

        # Segunda solicitação com a mesma chave
        destino2, criada2 = executar_operacao_unica(
            chave=chave,
            usuario=self.usuario,
            acao="entrada_estoque",
            dados=dados,
            executar=executar,
        )

        # Atualiza o objeto com os dados do banco
        self.produto.refresh_from_db()

        # O estoque deve aumentar somente uma vez
        self.assertEqual(self.produto.estoque, 20)

        # A primeira operação deve ser criada
        self.assertTrue(criada1)

        # A segunda operação não deve ser criada
        self.assertFalse(criada2)

        # As duas solicitações devem retornar o mesmo destino
        self.assertEqual(destino1, destino2)

        # Apenas uma operação deve existir
        self.assertEqual(
            OperacaoFormulario.objects.filter(
                chave=chave
            ).count(),
            1,
        )
class ReposicaoIntegracaoTest(TestCase):

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="admin_reposicao",
            password="SenhaTeste123!",
            is_staff=True,
        )

        self.client.force_login(self.usuario)

        self.produto = Produto.objects.create(
            nome="Arroz",
            codigo="ARR_TESTE",
            preco=Decimal("25.00"),
            estoque=10,
            estoque_minimo=3,
        )

    def test_reposicao_duplicada_pela_view(self):
        chave = str(uuid.uuid4())

        dados = {
            "produto": self.produto.pk,
            "quantidade": 10,
            "motivo": "Reposição de teste",
            "chave_operacao": chave,
        }

        url = reverse("entradas_estoque")

        primeira = self.client.post(url, dados)
        segunda = self.client.post(url, dados)

        self.produto.refresh_from_db()

        self.assertEqual(primeira.status_code, 302)
        self.assertEqual(segunda.status_code, 302)

        self.assertEqual(self.produto.estoque, 20)

        self.assertEqual(
            OperacaoFormulario.objects.filter(
                chave=chave
            ).count(),
            1,
        )
class VendaDuplicidadeTest(TestCase):

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="admin_vendas",
            password="SenhaTeste123!",
            is_staff=True,
        )

        self.client.force_login(self.usuario)

        self.produto = Produto.objects.create(
            nome="Café",
            codigo="CAF_TESTE",
            preco=Decimal("25.00"),
            estoque=20,
            estoque_minimo=3,
        )

    def test_venda_nao_pode_ser_duplicada(self):
        chave = str(uuid.uuid4())

        dados = {
            "cliente": "",
            "chave_operacao": chave,
            "itens-TOTAL_FORMS": "1",
            "itens-INITIAL_FORMS": "0",
            "itens-MIN_NUM_FORMS": "1",
            "itens-MAX_NUM_FORMS": "20",
            "itens-0-produto": str(self.produto.pk),
            "itens-0-quantidade": "2",
            "itens-0-preco_unitario": "25.00",
        }

        url = reverse("nova_venda")

        primeira = self.client.post(url, dados)
        segunda = self.client.post(url, dados)

        self.assertEqual(primeira.status_code, 302)
        self.assertEqual(segunda.status_code, 302)

        self.assertEqual(Venda.objects.count(), 1)

        self.assertEqual(
            OperacaoFormulario.objects.filter(
                chave=chave,
                acao="nova_venda",
            ).count(),
            1,
        )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.estoque, 20)

class RecebimentoDuplicidadeTest(TestCase):

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="admin_recebimento",
            password="SenhaTeste123!",
            is_staff=True,
        )

        self.client.force_login(self.usuario)

        self.produto = Produto.objects.create(
            nome="Café",
            codigo="CAF_RECEB",
            preco=Decimal("25.00"),
            estoque=20,
            estoque_minimo=3,
        )

        self.venda = Venda.objects.create(
            confirmada=True,
            cancelada=False,
        )

        ItemVenda.objects.create(
            venda=self.venda,
            produto=self.produto,
            quantidade=2,
            preco_unitario=Decimal("25.00"),
        )

    def test_recebimento_nao_pode_ser_duplicado(self):
        chave = str(uuid.uuid4())

        dados = {
            "acao": "receber",
            "valor": "25.00",
            "data": timezone.localdate().isoformat(),
            "chave_operacao": chave,
        }

        url = reverse(
            "detalhe_venda",
            kwargs={"pk": self.venda.pk},
        )

        primeira = self.client.post(url, dados)
        segunda = self.client.post(url, dados)

        self.assertEqual(primeira.status_code, 302)
        self.assertEqual(segunda.status_code, 302)

        movimentos = MovimentoCaixa.objects.filter(
            venda=self.venda,
            tipo="entrada",
        )

        self.assertEqual(movimentos.count(), 1)

        self.assertEqual(
            movimentos.first().valor,
            Decimal("25.00"),
        )

        self.assertEqual(
            OperacaoFormulario.objects.filter(
                chave=chave,
                acao="recebimento_venda",
            ).count(),
            1,
        )
class ReembolsoDuplicidadeTest(TestCase):

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="admin_reembolso",
            password="SenhaTeste123!",
            is_staff=True,
        )

        self.client.force_login(self.usuario)

        self.produto = Produto.objects.create(
            nome="Arroz",
            codigo="ARR_REEMB",
            preco=Decimal("25.00"),
            estoque=20,
            estoque_minimo=3,
        )

        self.venda = Venda.objects.create(
            confirmada=True,
            cancelada=True,
            motivo_cancelamento="Cancelamento para teste",
            data_cancelamento=timezone.now(),
            cancelada_por=self.usuario,
        )

        ItemVenda.objects.create(
            venda=self.venda,
            produto=self.produto,
            quantidade=2,
            preco_unitario=Decimal("25.00"),
        )

        MovimentoCaixa.objects.create(
            venda=self.venda,
            descricao="Recebimento anterior",
            tipo="entrada",
            valor=Decimal("50.00"),
            data=timezone.localdate(),
        )

    def test_reembolso_nao_pode_ser_duplicado(self):
        chave = str(uuid.uuid4())

        dados = {
            "acao": "reembolsar",
            "valor": "25.00",
            "data": timezone.localdate().isoformat(),
            "motivo": "Reembolso de teste",
            "chave_operacao": chave,
        }

        url = reverse(
            "detalhe_venda",
            kwargs={"pk": self.venda.pk},
        )

        primeira = self.client.post(url, dados)
        segunda = self.client.post(url, dados)

        self.assertEqual(primeira.status_code, 302)
        self.assertEqual(segunda.status_code, 302)

        movimentos = MovimentoCaixa.objects.filter(
            venda=self.venda,
            tipo="saida",
        )

        self.assertEqual(movimentos.count(), 1)

        self.assertEqual(
            movimentos.first().valor,
            Decimal("25.00"),
        )

        self.assertEqual(
            OperacaoFormulario.objects.filter(
                chave=chave,
                acao="reembolso_venda",
            ).count(),
            1,
        )
class MovimentoCaixaAdminTest(TestCase):

    def setUp(self):
        self.usuario = get_user_model().objects.create_superuser(
            username="admin_teste_caixa",
            password="SenhaTeste123!",
            email="admin@exemplo.com",
        )

        self.client.force_login(self.usuario)

        self.movimento = MovimentoCaixa.objects.create(
            descricao="Movimento para teste",
            tipo="entrada",
            valor=Decimal("100.00"),
            data=timezone.localdate(),
        )

    def test_admin_bloqueia_alteracoes_no_caixa(self):
        url_adicionar = reverse(
            "admin:gestao_movimentocaixa_add"
        )

        url_editar = reverse(
            "admin:gestao_movimentocaixa_change",
            args=[self.movimento.pk],
        )

        url_excluir = reverse(
            "admin:gestao_movimentocaixa_delete",
            args=[self.movimento.pk],
        )

        resposta_adicionar = self.client.get(url_adicionar)
        resposta_editar = self.client.get(url_editar)
        resposta_excluir = self.client.get(url_excluir)

        self.assertEqual(
            resposta_adicionar.status_code,
            403,
        )

        self.assertEqual(
            resposta_editar.status_code,
            200,
        )

        self.assertEqual(
            resposta_excluir.status_code,
            403,
        )

        # Tenta alterar o valor diretamente pelo Admin
        resposta_post = self.client.post(
        url_editar,
        {
            "descricao": "Movimento alterado",
            "tipo": "entrada",
            "valor": "999.00",
            "data": timezone.localdate().isoformat(),
            "venda": "",
        },
        )

        # A alteração deve ser proibida
        self.assertEqual(
        resposta_post.status_code,
        403,
        )

        # Confirma que o valor original permanece
        self.movimento.refresh_from_db()

        self.assertEqual(
            self.movimento.valor,
            Decimal("100.00"),
        )

        self.movimento.refresh_from_db()

        self.assertEqual(
            self.movimento.valor,
            Decimal("100.00"),
        )
class EstoqueInsuficienteTest(TestCase):

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="admin_estoque_teste",
            password="SenhaTeste123!",
            is_staff=True,
        )

        self.produto = Produto.objects.create(
            nome="Café",
            codigo="CAF_ESTOQUE",
            preco=Decimal("25.00"),
            estoque=5,
            estoque_minimo=3,
        )

        self.venda = Venda.objects.create()

        ItemVenda.objects.create(
            venda=self.venda,
            produto=self.produto,
            quantidade=10,
            preco_unitario=Decimal("25.00"),
        )

    def test_nao_confirmar_venda_sem_estoque(self):

        with self.assertRaisesMessage(
            ValueError,
            "Estoque insuficiente para Café.",
        ):
            confirmar_venda_com_estoque(
                venda_id=self.venda.pk,
                usuario=self.usuario,
            )

        # Atualiza os dados após a tentativa
        self.produto.refresh_from_db()
        self.venda.refresh_from_db()

        # O estoque deve continuar com 5 unidades
        self.assertEqual(
            self.produto.estoque,
            5,
        )

        # A venda não pode ficar confirmada
        self.assertFalse(
            self.venda.confirmada,
        )

        # Nenhuma saída deve ser registrada
        movimentos = MovimentoEstoque.objects.filter(
            venda=self.venda,
            tipo="saida",
        )

        self.assertEqual(
            movimentos.count(),
            0,
        )
class CancelamentoVendaTest(TestCase):

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="admin_cancelamento_teste",
            password="SenhaTeste123!",
            is_staff=True,
        )

        self.produto = Produto.objects.create(
            nome="Café",
            codigo="CAF_CANCELAMENTO",
            preco=Decimal("25.00"),
            estoque=20,
            estoque_minimo=3,
        )

        self.venda = Venda.objects.create()

        ItemVenda.objects.create(
            venda=self.venda,
            produto=self.produto,
            quantidade=5,
            preco_unitario=Decimal("25.00"),
        )

    def test_cancelamento_devolve_estoque_sem_duplicar(self):

        # Primeiro confirma a venda
        confirmar_venda_com_estoque(
            venda_id=self.venda.pk,
            usuario=self.usuario,
        )

        self.produto.refresh_from_db()
        self.venda.refresh_from_db()

        # Confirma que o estoque diminuiu
        self.assertEqual(
            self.produto.estoque,
            15,
        )

        self.assertTrue(
            self.venda.confirmada,
        )

        # Cancela a venda
        cancelar_venda_com_estoque(
            venda_id=self.venda.pk,
            usuario=self.usuario,
            motivo="Cancelamento para teste",
        )

        self.produto.refresh_from_db()
        self.venda.refresh_from_db()

        # O estoque deve voltar para 20
        self.assertEqual(
            self.produto.estoque,
            20,
        )

        # A venda deve estar cancelada
        self.assertTrue(
            self.venda.cancelada,
        )

        # Verifica o histórico de devolução
        movimentos = MovimentoEstoque.objects.filter(
            venda=self.venda,
            tipo="entrada",
            origem="cancelamento",
        )

        self.assertEqual(
            movimentos.count(),
            1,
        )

        self.assertEqual(
            movimentos.first().quantidade,
            5,
        )

        # Tenta cancelar a mesma venda novamente
        with self.assertRaises(ValueError):
            cancelar_venda_com_estoque(
                venda_id=self.venda.pk,
                usuario=self.usuario,
                motivo="Segundo cancelamento",
            )

        self.produto.refresh_from_db()

        # O estoque não pode aumentar novamente
        self.assertEqual(
            self.produto.estoque,
            20,
        )

        # Continua existindo apenas uma devolução
        self.assertEqual(
            MovimentoEstoque.objects.filter(
                venda=self.venda,
                origem="cancelamento",
            ).count(),
            1,
        )
class ReversaoEstoqueTest(TestCase):

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="admin_reversao_teste",
            password="SenhaTeste123!",
            is_staff=True,
        )

        self.cafe = Produto.objects.create(
            nome="Café",
            codigo="CAF_REVERSAO",
            preco=Decimal("25.00"),
            estoque=20,
            estoque_minimo=3,
        )

        self.arroz = Produto.objects.create(
            nome="Arroz",
            codigo="ARR_REVERSAO",
            preco=Decimal("10.00"),
            estoque=3,
            estoque_minimo=2,
        )

        self.venda = Venda.objects.create()

        ItemVenda.objects.create(
            venda=self.venda,
            produto=self.cafe,
            quantidade=5,
            preco_unitario=Decimal("25.00"),
        )

        ItemVenda.objects.create(
            venda=self.venda,
            produto=self.arroz,
            quantidade=10,
            preco_unitario=Decimal("10.00"),
        )

    def test_estoque_revertido_quando_um_produto_e_insuficiente(self):

        with self.assertRaises(ValueError):
            confirmar_venda_com_estoque(
                venda_id=self.venda.pk,
                usuario=self.usuario,
            )

        self.cafe.refresh_from_db()
        self.arroz.refresh_from_db()
        self.venda.refresh_from_db()

        # Nenhum produto deve perder estoque
        self.assertEqual(self.cafe.estoque, 20)
        self.assertEqual(self.arroz.estoque, 3)

        # A venda não deve ser confirmada
        self.assertFalse(self.venda.confirmada)

        # Nenhuma saída deve permanecer registrada
        self.assertEqual(
            MovimentoEstoque.objects.filter(
                venda=self.venda,
                tipo="saida",
            ).count(),
            0,
        )