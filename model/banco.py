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

    def executar_script(self, sql: str) -> ResultadoExecucao:
        if not self.__conexao or not self.__cursor:
            return ResultadoExecucao(
                False,
                "Conexão não estabelecida. Use o context manager (with)."
            )

        try:
            sql_limpo = sql.strip()
            if not sql_limpo:
                return ResultadoExecucao(False, "SQL vazio")

            self.__cursor.execute(sql_limpo)
            linhas_afetadas = self.__cursor.rowcount

            self.__conexao.commit()

            return ResultadoExecucao(
                True,
                "Script executado com sucesso",
                linhas_afetadas
            )

        except oracledb.Error as erro:
            if self.__conexao:
                self.__conexao.rollback()
            raise ExecucaoError.from_oracle_error(str(erro))

        except Exception as erro:
            if self.__conexao:
                self.__conexao.rollback()

            return ResultadoExecucao(
                False,
                f"Erro inesperado: {erro}"
            )

    def executar_scripts_batch(self, scripts: List[str]):
        resultados = []

        for script in scripts:
            try:
                resultado = self.executar_script(script)
                resultados.append(resultado)
            except ExecucaoError as e:
                resultados.append(ResultadoExecucao(False, str(e)))
                break

        return resultados

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