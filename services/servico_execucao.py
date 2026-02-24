from pathlib import Path
from typing import List
from model import Banco, ResultadoExecucao, ScriptProcessado, EstatisticasProcessamento
from model.excecoes import ConexaoError, ConfiguracaoError, ExecucaoError, SintaxeError, ObjetoError, PermissaoError


class ServicoExecucao:

    def __init__(self, stats: EstatisticasProcessamento, log_fn, progresso_fn):
        self.stats = stats
        self._log = log_fn
        self._progresso = progresso_fn

    def executar_script_em_cliente(self, script: ScriptProcessado, cliente: str) -> ResultadoExecucao:
        try:
            with Banco(cliente) as banco:
                if not banco.esta_conectado:
                    self._log('error', f"{script.nome_arquivo} -> {cliente}: Falha na conexão")
                    self.stats.scripts_com_erro += 1
                    return ResultadoExecucao(False, "Falha na conexão")

                resultados = banco.executar_scripts_batch(script.blocos)
                erros = [r for r in resultados if not r.sucesso]

                if not erros:
                    self._log('success', f"{script.nome_arquivo} -> {cliente}: Executado ({len(resultados)} bloco(s))")
                    self.stats.scripts_executados += 1
                else:
                    for r in erros:
                        self._log('error', f"{script.nome_arquivo} -> {cliente}: {r.mensagem}")
                    self.stats.scripts_com_erro += 1
                    self.stats.adicionar_erro(f"{script.nome_arquivo} -> {cliente}: {len(erros)} bloco(s) com erro")

                return resultados[-1] if resultados else ResultadoExecucao(False, "Nenhum bloco executado")

        except ConfiguracaoError as e:
            self._log('error', f"{cliente}: Configuração incompleta — {e}")
            self.stats.scripts_com_erro += 1
            self.stats.adicionar_erro(f"{cliente}: {e}")
            return ResultadoExecucao(False, str(e))

        except ConexaoError as e:
            self._log('error', f"{cliente}: Falha de conexão — {e}")
            self.stats.scripts_com_erro += 1
            self.stats.adicionar_erro(f"{cliente}: {e}")
            return ResultadoExecucao(False, str(e))

        except SintaxeError as e:
            self._log('error', f"{script.nome_arquivo} -> {cliente}: Erro de sintaxe ({e.codigo_ora}) — {e}")
            self.stats.scripts_com_erro += 1
            self.stats.adicionar_erro(f"{script.nome_arquivo} -> {cliente}: {e}")
            return ResultadoExecucao(False, str(e))

        except ObjetoError as e:
            self._log('error', f"{script.nome_arquivo} -> {cliente}: Objeto não encontrado ({e.codigo_ora}) — {e}")
            self.stats.scripts_com_erro += 1
            self.stats.adicionar_erro(f"{script.nome_arquivo} -> {cliente}: {e}")
            return ResultadoExecucao(False, str(e))

        except ExecucaoError as e:
            self._log('error', f"{script.nome_arquivo} -> {cliente}: Erro de execução ({e.codigo_ora}) — {e}")
            self.stats.scripts_com_erro += 1
            self.stats.adicionar_erro(f"{script.nome_arquivo} -> {cliente}: {e}")
            return ResultadoExecucao(False, str(e))

        except Exception as e:
            self._log('error', f"{script.nome_arquivo} -> {cliente}: Exceção - {str(e)}")
            self.stats.scripts_com_erro += 1
            self.stats.adicionar_erro(f"{script.nome_arquivo} -> {cliente}: Exceção - {str(e)}")
            return ResultadoExecucao(False, f"Exceção: {str(e)}")

    def processar_lote(self, diretorio: Path, clientes: List[str], scripts: List[ScriptProcessado]):
        self._log('info', f"Executando {len(scripts)} script(s) em {len(clientes)} cliente(s)")

        total_operacoes = len(scripts) * len(clientes)
        operacao_atual = 0
        resultados_execucao = {}

        for script in scripts:
            resultados_script = {}

            for cliente in clientes:
                operacao_atual += 1
                self._progresso(operacao_atual, total_operacoes, f"{script.nome_arquivo} -> {cliente}")
                resultado = self.executar_script_em_cliente(script, cliente)
                resultados_script[cliente] = resultado

            resultados_execucao[script.nome_arquivo] = resultados_script

        return resultados_execucao