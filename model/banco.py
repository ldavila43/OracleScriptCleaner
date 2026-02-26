import re
import oracledb
import os
from dotenv import load_dotenv
from typing import Optional, List
from model.excecoes import ConexaoError, ConfiguracaoError, ExecucaoError
from model.data_classes import ResultadoExecucao

class Banco:
    _env_carregado = False
    _thick_mode_ativado = False

    def __init__(self, cliente: str):
        if not Banco._env_carregado:
            load_dotenv()
            Banco._env_carregado = True

        if not Banco._thick_mode_ativado:
            try:
                oracledb.init_oracle_client()
                Banco._thick_mode_ativado = True
            except Exception as e:
                raise RuntimeError(f"Falha ao carregar Oracle Instant Client: {e}")

        self.__cliente = cliente
        self.__conexao: Optional[oracledb.Connection] = None
        self.__cursor: Optional[oracledb.Cursor] = None

    def __enter__(self):
        try:
            db_host = os.getenv(f"{self.__cliente}_HOST")
            db_port = os.getenv("PORT", "1521")
            db_user = os.getenv(f"{self.__cliente}_USER")
            db_pass = os.getenv(f"{self.__cliente}_PASSWORD")
            db_service = os.getenv(f"{self.__cliente}_SERVICE")

            if not all([db_host, db_user, db_pass, db_service]):
                campos_faltando = []
                if not db_host: campos_faltando.append(f"{self.__cliente}_HOST")
                if not db_user: campos_faltando.append(f"{self.__cliente}_USER")
                if not db_pass: campos_faltando.append(f"{self.__cliente}_PASSWORD")
                if not db_service: campos_faltando.append(f"{self.__cliente}_SERVICE")

                raise ConfiguracaoError(
                    f"Configurações incompletas para {self.__cliente}. "
                    f"Faltando: {', '.join(campos_faltando)}"
                )

            dsn_montado = f"{db_host}:{db_port}/{db_service}"
            self.__conexao = oracledb.connect(
                user=db_user,
                password=db_pass,
                dsn=dsn_montado
            )
            self.__cursor = self.__conexao.cursor()
            return self

        except oracledb.Error as erro:
            raise ConexaoError(f"Erro ao conectar no banco {self.__cliente}: {erro}") from erro
        except Exception as erro:
            raise RuntimeError(
                f"Erro inesperado ao configurar conexão para {self.__cliente}: {erro}"
            ) from erro

    def _extrair_nome_objeto(self, sql: str) -> Optional[tuple[str, str]]:
        match = re.search(
            r'CREATE\s+(?:OR\s+REPLACE\s+)?(PROCEDURE|FUNCTION|PACKAGE\s+BODY|PACKAGE|TRIGGER|TYPE)\s+(\w+)',
            sql,
            re.IGNORECASE
        )
        if match:
            tipo = re.sub(r'\s+', ' ', match.group(1)).strip().upper()
            nome = match.group(2).strip().upper()
            return nome, tipo
        return None

    def _verificar_erros_compilacao(self, nome_objeto: str) -> List[str]:
        try:
            self.__cursor.execute(
                """
                SELECT line, position, text
                FROM user_errors
                WHERE name = :nome
                ORDER BY sequence
                """,
                nome=nome_objeto
            )
            rows = self.__cursor.fetchall()
            return [f"Linha {row[0]}, Col {row[1]}: {row[2].strip()}" for row in rows]
        except Exception:
            return []

    def executar_funcao(self, nm_funcao):
        if self.__cursor:
            self.__cursor.execute(f"SELECT {nm_funcao} FROM DUAL")
            resultado = self.__cursor.fetchone()
            return resultado[0] if resultado else None
        return None

    def executar_script(self, sql: str) -> ResultadoExecucao:
        if not self.__conexao or not self.__cursor:
            return ResultadoExecucao(False, "Conexão não estabelecida. Use o context manager (with).")

        try:
            sql_limpo = sql.strip()
            if not sql_limpo:
                return ResultadoExecucao(False, "SQL vazio")

            resultado_objeto = self._extrair_nome_objeto(sql_limpo)

            self.__cursor.execute(sql_limpo)
            linhas_afetadas = self.__cursor.rowcount
            self.__conexao.commit()

            if resultado_objeto:
                nome_objeto, tipo_objeto = resultado_objeto
                tipos_com_body = {'PACKAGE BODY', 'PROCEDURE', 'FUNCTION', 'TRIGGER', 'TYPE'}
                if tipo_objeto in tipos_com_body:
                    self.__cursor.execute(
                        """
                        SELECT status FROM user_objects
                        WHERE object_name = :nome
                        AND status = 'INVALID'
                        """,
                        nome=nome_objeto
                    )
                    row = self.__cursor.fetchone()
                    if row:
                        erros_compilacao = self._verificar_erros_compilacao(nome_objeto)
                        if erros_compilacao:
                            detalhes = '\n'.join(erros_compilacao)
                            return ResultadoExecucao(
                                False,
                                f"Objeto '{nome_objeto}' compilado com erros:\n{detalhes}"
                            )

            return ResultadoExecucao(True, "Script executado com sucesso", linhas_afetadas)

        except oracledb.Error as erro:
            if self.__conexao:
                self.__conexao.rollback()
            raise ExecucaoError.from_oracle_error(str(erro))

        except Exception as erro:
            if self.__conexao:
                self.__conexao.rollback()
            return ResultadoExecucao(False, f"Erro inesperado: {erro}")

    def executar_scripts_batch(self, scripts: List[str]):
        resultados = []

        for script in scripts:
            try:
                resultado = self.executar_script(script)
                resultados.append(resultado)
            except ExecucaoError as e:
                resultados.append(ResultadoExecucao(False, str(e)))
            except Exception as e:
                resultados.append(ResultadoExecucao(False, f"Erro inesperado no bloco: {e}"))

        return resultados

    def atualizar_versao_banco(self, ultimo_script):
        if self.__cursor:
            self.__cursor.execute(f"""
            create or replace FUNCTION busca_versao_banco RETURN VARCHAR2 IS
            BEGIN
                RETURN '{ultimo_script}';
            END busca_versao_banco;
            """)

            self.__conexao.commit()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.__cursor:
                self.__cursor.close()
                self.__cursor = None
        except Exception as e:
            print(f"Aviso: Erro ao fechar cursor: {e}")

        try:
            if self.__conexao:
                self.__conexao.close()
                self.__conexao = None
        except Exception as e:
            print(f"Aviso: Erro ao fechar conexão: {e}")
        return False

    @property
    def cliente(self) -> str:
        return self.__cliente

    @property
    def esta_conectado(self) -> bool:
        return self.__conexao is not None and self.__cursor is not None