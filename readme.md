# Executor de Scripts SQL

Ferramenta desktop para execução em lote de scripts SQL/PL-SQL em bancos de dados Oracle, com suporte a múltiplos clientes, sanitização automática de encoding e interface gráfica.

---

## Funcionalidades

- Execução de scripts `.sql` em múltiplos bancos Oracle simultaneamente
- Sanitização automática de encoding (UTF-8, ISO-8859-1, Windows-1252, double-encoding)
- Suporte completo a blocos PL/SQL, DDL e DML com separação correta por `/`
- Tratamento de exceções Oracle tipadas (sintaxe, objeto não encontrado, permissão)
- Log de execução em tempo real com cores por tipo de mensagem
- Interface gráfica com painel de log redimensionável
- Modo "apenas processar" para validar scripts sem executar no banco

---

## Estrutura do Projeto

```
projetos/
├── main.py
├── requirements.txt
├── clientes.json               # Lista de clientes disponíveis
├── .env                        # Credenciais dos bancos (não versionar)
│
├── config/
│   ├── __init__.py
│   └── configuracao.py         # Leitura do .env e clientes.json
│
├── controller/
│   ├── __init__.py
│   └── controlador.py          # Orquestração entre serviços e view
│
├── model/
│   ├── __init__.py
│   ├── banco.py                # Conexão e execução Oracle
│   ├── data_classes.py         # Dataclasses do domínio
│   ├── encoder.py              # Sanitização de encoding
│   └── excecoes.py             # Hierarquia de exceções do sistema
│
├── services/
│   ├── __init__.py
│   ├── servico_arquivo.py      # Listagem, limpeza e validação de scripts
│   └── servico_execucao.py     # Execução dos scripts no banco
│
└── view/
    ├── __init__.py
    ├── view_interface.py       # Interface abstrata da view (ABC)
    ├── style.py                # Estilo QSS da interface
    └── tela.py                 # Interface gráfica PyQt6
```

---

## Pré-requisitos

- Python 3.11+
- Oracle Instant Client instalado e configurado no PATH
- Acesso de rede aos bancos Oracle configurados

---

## Instalação

**1. Clone o repositório e acesse a pasta:**
```bash
cd projetos
```

**2. Crie e ative o ambiente virtual:**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

**3. Instale as dependências:**
```bash
pip install -r requirements.txt
```

**4. Configure o `.env`** com as credenciais de cada cliente:
```env
PORT=1521

LOCALHOST_HOST=192.168.0.1
LOCALHOST_USER=usuario
LOCALHOST_PASSWORD=senha
LOCALHOST_SERVICE=ORCL

CONEXAO_HOST=192.168.0.2
CONEXAO_USER=usuario
CONEXAO_PASSWORD=senha
CONEXAO_SERVICE=ORCL
```

**5. Configure o `clientes.json`** com os nomes dos clientes disponíveis:
```json
[
    "LOCALHOST",
    "CONEXAO",
    "BANCO"
]
```

> ⚠️ O nome de cada cliente no `clientes.json` deve corresponder exatamente ao prefixo das variáveis no `.env`.

---

## Uso

```bash
python main.py
```

**Fluxo de uso:**

1. Selecione o diretório contendo os arquivos `.sql`
2. Selecione os clientes onde os scripts serão executados
3. Opcional: marque **"Apenas processar"** para sanitizar os arquivos sem executar no banco
4. Clique em **Executar** e acompanhe o log em tempo real

---

## Formato dos Scripts

Os scripts devem seguir o padrão Oracle SQL\*Plus, com blocos separados por `/`:

```sql
-- DDL simples
CREATE TABLE exemplo (
    id     NUMBER PRIMARY KEY,
    nome   VARCHAR2(100)
);
/

-- Bloco PL/SQL
BEGIN
    INSERT INTO exemplo VALUES (1, 'teste');
    COMMIT;
END;
/

-- Package
CREATE OR REPLACE PACKAGE pkg_exemplo IS
    PROCEDURE executar;
END pkg_exemplo;
/
```

> Blocos DDL sem `/` também são suportados — o sistema os divide automaticamente pelo `;`.

---

## Hierarquia de Exceções

```
SqlExecutorError
├── ConfiguracaoError       # Credenciais ausentes no .env
├── ConexaoError            # Falha ao conectar no banco
├── ExecucaoError           # Erro genérico ao executar script
│   ├── SintaxeError        # ORA-00900, ORA-06550 — erro de sintaxe
│   ├── ObjetoError         # ORA-00942 — tabela ou objeto não encontrado
│   └── PermissaoError      # ORA-01031 — privilégios insuficientes
└── ArquivoError            # Erro ao ler ou processar arquivo .sql
```

---

## Arquitetura

O projeto segue o padrão **MVC** com separação em camadas:

- **Model** — estruturas de dados, conexão com banco, encoding e exceções
- **Services** — regras de negócio (processamento de arquivos e execução)
- **Controller** — orquestra os serviços e faz a ponte com a view
- **View** — interface gráfica PyQt6, desacoplada via `ViewInterface`

A `ViewInterface` é uma classe abstrata que permite trocar a interface gráfica sem alterar nenhuma outra camada do sistema.

---

## Dependências

| Pacote | Versão | Uso |
|--------|--------|-----|
| `oracledb` | >=3.4.1 | Conexão com Oracle |
| `python-dotenv` | >=1.2.1 | Leitura do `.env` |
| `chardet` | >=5.2.0 | Detecção de encoding |
| `PyQt6` | >=6.6.0 | Interface gráfica |

---