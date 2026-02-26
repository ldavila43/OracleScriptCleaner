import oracledb
from typing import List
from model.banco import Banco
from model.data_classes import ResultadoExecucao
from model.excecoes import ExecucaoError
from services.inspetor_oracle import InspetorOracle


class ExecutorSql:

    def __init__(self, banco: Banco):
        self._banco = banco
        self._inspetor = InspetorOracle(banco)

    def executar_script(self, sql: str) -> ResultadoExecucao:
        sql_limpo = sql.strip()
        if not sql_limpo:
            return ResultadoExecucao(False, "SQL vazio")

        try:
            resultado_objeto = self._inspetor.extrair_nome_objeto(sql_limpo)

            linhas_afetadas = self._banco.executar_bloco(sql_limpo)
            self._banco.commit()

            if resultado_objeto:
                nome_objeto, tipo_objeto = resultado_objeto
                if self._inspetor.requer_inspecao(tipo_objeto) and self._inspetor.objeto_invalido(nome_objeto):
                    erros = self._inspetor.verificar_erros_compilacao(nome_objeto)
                    if erros:
                        return ResultadoExecucao(
                            False,
                            f"Objeto '{nome_objeto}' compilado com erros:\n" + '\n'.join(erros)
                        )

            return ResultadoExecucao(True, "Script executado com sucesso", linhas_afetadas)

        except oracledb.Error as erro:
            self._banco.rollback()
            raise ExecucaoError.from_oracle_error(str(erro))

        except Exception as erro:
            self._banco.rollback()
            return ResultadoExecucao(False, f"Erro inesperado: {erro}")

    def executar_lote(self, blocos: List[str]) -> List[ResultadoExecucao]:
        resultados = []
        for bloco in blocos:
            try:
                resultado = self.executar_script(bloco)
                resultados.append(resultado)
            except ExecucaoError as e:
                resultados.append(ResultadoExecucao(False, str(e)))
            except Exception as e:
                resultados.append(ResultadoExecucao(False, f"Erro inesperado no bloco: {e}"))
        return resultados

    def executar_funcao(self, nm_funcao: str):
        self._banco.executar_query(f"SELECT {nm_funcao} FROM DUAL")
        resultado = self._banco.fetchone()
        return resultado[0] if resultado else None

    def atualizar_versao_banco(self, ultimo_script: str):
        self._banco.executar_bloco(f"""
            CREATE OR REPLACE FUNCTION busca_versao_banco RETURN VARCHAR2 IS
            BEGIN
                RETURN '{ultimo_script}';
            END busca_versao_banco;
        """)
        self._banco.commit()