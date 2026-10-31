# Sistema de Gestão para Pequenos Negócios

Sistema web para controle de vendas, estoque, clientes e movimentos de caixa,
com dashboard e filtro por período.

Projeto desenvolvido para o Tema 6 — Sistema de Gestão para Pequenos Negócios.

## Funcionalidades

### Produtos
- Listagem e pesquisa por nome ou código.
- Cadastro com estoque inicial.
- Edição de nome, código, preço e estoque mínimo.
- Preservação do estoque atual no formulário de edição.
- Bloqueio de códigos duplicados.
- Identificação de produtos com estoque baixo.

### Clientes
- Listagem e pesquisa por nome, telefone ou e-mail.
- Cadastro e edição.
- Nome obrigatório, com telefone e e-mail opcionais.

### Vendas
- Listagem e pesquisa por número ou nome do cliente.
- Cadastro com cliente opcional e vários produtos.
- Registro da quantidade e do preço unitário de cada item.
- Cálculo do total da venda.
- Confirmação com baixa de estoque.
- Bloqueio quando não há estoque suficiente.
- Proteção contra confirmação duplicada.

### Caixa
- Consulta dos movimentos.
- Pesquisa por descrição e filtro por tipo.
- Cadastro manual de entradas e saídas.
- Cálculo das entradas, saídas e resultado dos movimentos encontrados.

### Dashboard
- Quantidade atual de produtos e clientes.
- Quantidade de vendas confirmadas.
- Faturamento das vendas confirmadas.
- Entradas, saídas e resultado do caixa.
- Filtro por data inicial e final.
- Listagem de produtos com estoque igual ou inferior ao mínimo.

## Tecnologias

- Python.
- Django.
- SQLite.
- HTML e CSS.
- Git e GitHub.

## Ambiente utilizado

O projeto foi desenvolvido no Windows, com Python 3.14.3,
PowerShell e Visual Studio Code.

As versões das dependências estão registradas em `requirements.txt`.

## Instalação e execução

Os comandos abaixo são para Windows com PowerShell.
Execute uma linha por vez.

### 1. Baixar o projeto

Tenha Python e Git instalados.
Se o repositório estiver privado, sua conta precisa ter acesso.

```powershell
git clone https://github.com/matheuzdbatista/gestao-negocio.git
```

Entre na pasta:

```powershell
cd gestao-negocio
```

Todos os próximos comandos devem ser executados nessa pasta,
onde estão `manage.py` e `requirements.txt`.

### 2. Criar o ambiente Python

```powershell
python -m venv .venv
```

### 3. Instalar as dependências

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Os comandos usam diretamente o Python do ambiente.
Não é necessário ativá-lo.

### 4. Criar o banco de dados

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

As migrações necessárias estão incluídas no repositório.

### 5. Criar um administrador

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Preencha o nome de usuário e a senha.
O e-mail pode ficar vazio.

A senha não aparece enquanto é digitada no terminal.

### 6. Verificar o projeto

```powershell
.\.venv\Scripts\python.exe manage.py check
```

### 7. Iniciar o servidor

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Abra:

http://127.0.0.1:8000/

Entre com o administrador criado anteriormente.
Mantenha o terminal aberto durante o uso.

Para parar o servidor, pressione Ctrl + C.

## Páginas do sistema

| Página | Endereço local |
|---|---|
| Dashboard | http://127.0.0.1:8000/ |
| Produtos | http://127.0.0.1:8000/produtos/ |
| Novo produto | http://127.0.0.1:8000/produtos/novo/ |
| Clientes | http://127.0.0.1:8000/clientes/ |
| Novo cliente | http://127.0.0.1:8000/clientes/novo/ |
| Vendas | http://127.0.0.1:8000/vendas/ |
| Nova venda | http://127.0.0.1:8000/vendas/nova/ |
| Caixa | http://127.0.0.1:8000/caixa/ |
| Novo movimento | http://127.0.0.1:8000/caixa/novo/ |
| Administração | http://127.0.0.1:8000/admin/ |

## Como usar

### Produtos

1. Acesse Produtos.
2. Clique em Novo produto.
3. Informe nome, código, preço, estoque inicial e estoque mínimo.
4. Salve.

Para alterar os dados, use Editar na lista.
O formulário de edição mantém o estoque atual.

### Clientes

1. Acesse Clientes.
2. Clique em Novo cliente.
3. Informe o nome e, opcionalmente, telefone e e-mail.
4. Salve.

Use Editar para atualizar os dados.

### Vendas

1. Acesse Vendas e clique em Nova venda.
2. Selecione um cliente, se desejar.
3. Preencha pelo menos um produto.
4. Informe quantidade e preço unitário.
5. Deixe as linhas não utilizadas como estão.
6. Clique em Salvar venda.
7. Confira o registro na lista.
8. Clique em Confirmar venda para baixar o estoque.

Salvar uma venda não a confirma automaticamente.

### Caixa

1. Acesse Movimentos de caixa.
2. Clique em Novo movimento.
3. Informe descrição, tipo, valor e data.
4. Salve.

Use Entrada para recebimentos e Saída para despesas.
O valor deve ser sempre positivo.

Registre recebimentos apenas quando o dinheiro for efetivamente recebido.
A confirmação de uma venda não cria um movimento de caixa automaticamente.

## Regras de funcionamento

- O código de cada produto deve ser único.
- O preço nos formulários próprios de produtos deve ser maior que zero.
- Cada venda deve ter pelo menos um item.
- Quantidades e preços dos itens devem ser positivos.
- O preço unitário fica registrado no item da venda.
- Alterar o preço do produto não altera o preço das vendas anteriores.
- Salvar uma venda não altera o estoque.
- Confirmar uma venda baixa o estoque uma única vez.
- Se um produto aparecer em mais de uma linha, suas quantidades são somadas
  para verificar e descontar o estoque.
- Se faltar estoque em qualquer produto, a venda não é confirmada
  e nenhum item daquela venda é descontado.
- Vendas confirmadas não podem ser editadas nem excluídas pelo painel administrativo.
- Vendas não confirmadas podem ser excluídas individualmente
  pelo painel administrativo.
- Excluir uma venda não confirmada remove seus itens,
  preservando os produtos cadastrados.
- Os movimentos de caixa são registrados manualmente.

## Indicadores e filtros

### Faturamento

É a soma de quantidade × preço unitário dos itens das vendas confirmadas.

Faturamento não representa necessariamente dinheiro recebido nem lucro.

### Caixa

- Entradas: soma dos movimentos do tipo Entrada.
- Saídas: soma dos movimentos do tipo Saída.
- Resultado: entradas menos saídas.

O resultado não considera um saldo inicial.

Na tela de caixa, os totais acompanham a pesquisa por descrição
e o filtro por tipo.

### Período no dashboard

- Vendas são filtradas pela data de criação.
- Caixa é filtrado pela data informada no movimento.
- As datas inicial e final são incluídas na consulta.
- É possível informar apenas uma das datas.
- Datas inválidas ou invertidas exibem um aviso.
- O resultado do período não inclui saldo anterior.
- Produtos, clientes e alertas de estoque mostram a situação atual,
  independentemente do período selecionado.

## Acesso

As telas próprias exigem um usuário autenticado, ativo e com acesso
administrativo (`is_staff`).

O administrador criado por `createsuperuser` possui esse acesso.

Esta versão não diferencia funções como vendedor, caixa e gerente
nas telas próprias.

## Estrutura principal

- `config/settings.py`: configurações do Django.
- `config/urls.py`: endereços das páginas.
- `gestao/models.py`: estrutura dos dados.
- `gestao/forms.py`: formulários e validações.
- `gestao/views.py`: processamento das páginas.
- `gestao/admin.py`: configurações do painel administrativo.
- `gestao/templates/gestao/`: páginas HTML e estilos.
- `gestao/migrations/`: histórico da estrutura do banco.
- `manage.py`: comandos de gerenciamento.
- `requirements.txt`: dependências do projeto.

## Dados e backup

O arquivo `db.sqlite3` guarda os cadastros locais.
Ele não é enviado ao GitHub.

A pasta `.venv` também não é versionada.

Uma nova instalação começa sem os registros e sem o administrador
do computador original.

O GitHub preserva o código. O banco precisa de backup separado.

Para uma cópia local dos dados, pare o servidor e copie o arquivo
`db.sqlite3` para um local seguro.

## Verificações

Verificar a configuração:

```powershell
.\.venv\Scripts\python.exe manage.py check
```

Verificar se há alterações de modelos sem migração:

```powershell
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Esses comandos não substituem os testes das funcionalidades.

### Testes manuais realizados durante o desenvolvimento

- Cadastro, pesquisa e edição de produtos.
- Bloqueio de código de produto duplicado.
- Preservação do estoque na edição de produtos.
- Cadastro, pesquisa e edição de clientes.
- Pesquisa de vendas por cliente e número.
- Cadastro de venda com vários itens.
- Cálculo do total da venda.
- Confirmação com baixa de estoque.
- Bloqueio de confirmação duplicada pelo painel administrativo.
- Bloqueio por estoque insuficiente pelo painel administrativo.
- Cadastro de movimentos de caixa.
- Filtro de movimentos por tipo.
- Atualização dos indicadores do dashboard.
- Filtro por período, período sem registros e datas invertidas.
- Exibição e remoção do alerta de estoque baixo.
- Instalação de uma versão anterior em uma cópia limpa do repositório.

## Limitações da versão inicial

- A tela de nova venda apresenta três linhas de produtos,
  sem botão para adicionar outras linhas.
- O preço unitário da venda é preenchido manualmente.
- Não há tela própria para editar vendas.
- Não há cancelamento de venda confirmada com devolução de estoque.
- Não há histórico separado de movimentações de estoque.
- Recebimentos não possuem vínculo automático com as vendas.
- Não há controle automático de parcelas ou de valores a receber.
- Não há proteção específica contra criação de lançamentos de caixa duplicados.
- A tela própria de caixa oferece consulta e cadastro;
  alterações e exclusões ficam no painel administrativo.
- As listas não possuem paginação.
- O relatório não calcula lucro.
- Ainda não foi criada uma suíte de testes automatizados.

## Desenvolvimento local

Esta versão está configurada para desenvolvimento local,
com o servidor de desenvolvimento do Django.

Antes de publicar na internet, é necessário revisar a implantação,
configurar uma chave secreta própria fora do código,
desativar DEBUG e configurar os hosts permitidos.