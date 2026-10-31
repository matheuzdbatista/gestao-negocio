# Sistema de Gestão para Pequenos Negócios

Projeto de um sistema web para controle de produtos, clientes, vendas,
estoque e movimentos de caixa, com dashboard e filtro por período.

## Funcionalidades

- Cadastro e pesquisa de produtos e clientes.
- Registro de vendas com vários produtos.
- Cálculo do total de cada venda.
- Confirmação de vendas com baixa de estoque.
- Bloqueio de confirmação quando não há estoque suficiente.
- Proteção contra baixa duplicada da mesma venda.
- Bloqueio de edição de vendas confirmadas no painel administrativo.
- Registro manual de entradas e saídas de caixa.
- Dashboard com faturamento, vendas confirmadas e resultado do caixa.
- Filtro por data inicial e final.
- Listagem de produtos com estoque igual ou inferior ao mínimo.
- Acesso ao dashboard restrito a usuários administrativos.

## Tecnologias

- Python.
- Django.
- SQLite.
- HTML e CSS.
- Git e GitHub.

## Ambiente utilizado

O projeto foi desenvolvido com Python 3.14.3 no Windows,
usando PowerShell e Visual Studio Code.

As versões dos pacotes estão registradas em `requirements.txt`.

## Como instalar e executar

Os comandos abaixo são para Windows com PowerShell.
Execute uma linha por vez.

### 1. Baixar o projeto

É necessário ter Python e Git instalados.
Se o repositório estiver privado, sua conta precisa ter acesso.

```powershell
git clone https://github.com/matheuzdbatista/gestao-negocio.git
cd gestao-negocio
```

### 2. Criar o ambiente Python

```powershell
python -m venv .venv
```

### 3. Instalar as dependências

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Não é necessário ativar o ambiente, pois os comandos usam diretamente
o Python da pasta `.venv`.

### 4. Criar o banco de dados

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

As migrações já estão incluídas no projeto.

### 5. Criar o usuário administrador

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Siga as instruções do terminal.
A senha não aparece enquanto é digitada.

### 6. Verificar a configuração

```powershell
.\.venv\Scripts\python.exe manage.py check
```

### 7. Iniciar o servidor

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Acesse:

- Dashboard: http://127.0.0.1:8000/
- Administração: http://127.0.0.1:8000/admin/

Use o usuário administrador criado anteriormente.
Mantenha o terminal aberto enquanto utiliza o sistema.
Para parar o servidor, pressione Ctrl + C.

## Como usar

1. Cadastre produtos com preço e quantidade disponível.
2. Cadastre os clientes, se necessário.
3. Adicione uma venda e seus itens no painel administrativo.
4. Preencha manualmente o preço unitário de cada item.
5. Salve a venda.
6. Na lista de vendas, selecione a venda e execute a ação
   "Confirmar vendas e baixar estoque".
7. Registre no caixa os recebimentos e despesas efetivamente realizados.
8. Consulte os indicadores no dashboard.

## Regras de funcionamento

- Salvar uma venda não baixa o estoque.
- Confirmar uma venda baixa o estoque uma única vez.
- Se faltar estoque em qualquer produto, a venda não é confirmada
  e nenhum item daquela venda é descontado.
- O preço unitário fica registrado no item da venda, preservando
  o valor vendido quando o preço do produto muda.
- Vendas confirmadas não podem ser editadas pelo painel administrativo.
- A exclusão de vendas está desabilitada no painel.
- Confirmar uma venda não cria automaticamente uma entrada no caixa.
- Os movimentos de caixa são cadastrados manualmente.

## Indicadores e filtro por período

- Faturamento: soma dos itens das vendas confirmadas.
- Entradas: soma dos movimentos de caixa do tipo entrada.
- Saídas: soma dos movimentos de caixa do tipo saída.
- Resultado do período: entradas menos saídas.
- Faturamento não representa dinheiro recebido nem lucro.
- O resultado do caixa não inclui saldo anterior ao período selecionado.

O filtro de vendas usa a data de criação da venda.
O filtro de caixa usa a data informada no movimento.
As datas inicial e final são incluídas na consulta.

As quantidades de produtos e clientes e os alertas de estoque
mostram a situação atual, independentemente do filtro.

## Dados e backup

O arquivo `db.sqlite3` guarda os cadastros locais e não é enviado ao GitHub.
A pasta `.venv` também não é versionada.

Uma nova instalação começa sem os registros e sem o usuário administrador
do computador original.

O GitHub preserva o código; o backup do banco precisa ser feito separadamente,
com o servidor parado.

## Limitações da versão inicial

- Recebimentos não possuem vínculo automático com as vendas.
- Não há cancelamento de venda com devolução de estoque.
- Não há histórico separado das movimentações de estoque.
- Os cadastros e as vendas utilizam o painel administrativo do Django.

## Desenvolvimento local

Esta versão está configurada para desenvolvimento local.
Antes de publicar na internet, é necessário configurar uma chave secreta
própria, desativar DEBUG e revisar as configurações de implantação.