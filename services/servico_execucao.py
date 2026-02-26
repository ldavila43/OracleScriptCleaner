from datetime import datetime
from pathlib import Path
from typing import List
from model import Banco, ResultadoExecucao, ScriptProcessado, EstatisticasProcessamento
from model.excecoes import ConexaoError, ConfiguracaoError, ExecucaoError, SintaxeError, ObjetoError, PermissaoError


class ServicoExecucao:

    def __init__(self, stats: EstatisticasProcessamento, log_fn, progresso_fn):
        self.stats = stats
        self._log = log_fn
        self._progresso = progresso_fn

    def _is_ignorable(self, mensagem: str) -> bool:
        import re
        from model.excecoes import ExecucaoError
        match = re.search(r'ORA-(\d+)', mensagem)
        if not match:
            return False
        codigo = f'ORA-{match.group(1)}'
        temp = ExecucaoError("", codigo)
        return temp.is_ignorable

    def _buscar_versao_cliente(self, cliente: str) -> str | None:
        try:
            with Banco(cliente) as banco:
                return banco.executar_funcao('busca_versao_banco')
        except Exception as e:
            self._log('warning', f"{cliente}: Não foi possível obter versão do banco — executando todos os scripts. ({e})")
            return None

    def _atualizar_versao_cliente(self, cliente: str, nome_script: str):
        try:
            with Banco(cliente) as banco:
                banco.atualizar_versao_banco(nome_script)
            self._log('info', f"{cliente}: Versão atualizada para {nome_script}")
        except Exception as e:
            self._log('warning', f"{cliente}: Não foi possível atualizar versão no banco. ({e})")

    def executar_script_em_cliente(self, script: ScriptProcessado, cliente: str) -> ResultadoExecucao:
        try:
            with Banco(cliente) as banco:
                if not banco.esta_conectado:
                    self._log('error', f"{script.nome_arquivo} -> {cliente}: Falha na conexão")
                    self.stats.scripts_com_erro += 1
                    return ResultadoExecucao(False, "Falha na conexão")

                resultados = banco.executar_scripts_batch(script.blocos)

                sucessos = [r for r in resultados if r.sucesso]
                erros = [r for r in resultados if not r.sucesso]
                erros_criticos = [r for r in erros if not self._is_ignorable(r.mensagem)]
                erros_ignoraveis = [r for r in erros if self._is_ignorable(r.mensagem)]

                for i, r in enumerate(resultados):
                    if not r.sucesso:
                        if self._is_ignorable(r.mensagem):
                            self._log('info', f"  └─ Bloco {i + 1} ignorado: {r.mensagem.splitlines()[0]}")
                        else:
                            self._log('error', f"  └─ Bloco {i + 1} falhou: {r.mensagem}")

                if not erros_criticos:
                    self._log('success',
                              f"{script.nome_arquivo} -> {cliente}: Executado ({len(sucessos)} bloco(s) ok, {len(erros_ignoraveis)} ignorado(s))")
                    self.stats.scripts_executados += 1
                    return resultados[-1]

                msg_resumo = f"{len(erros_criticos)} erro(s) crítico(s) em {len(resultados)} bloco(s)"
                self._log('warning', f"{script.nome_arquivo} -> {cliente}: Finalizado com {msg_resumo}")
                self.stats.scripts_com_erro += 1
                self.stats.adicionar_erro(f"{script.nome_arquivo} -> {cliente}: {msg_resumo}")
                return erros_criticos[0]

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

    def _gravar_erros(self, diretorio: Path, clientes: List[str], erros: List[str]):
        caminho = Path(__file__).parent.parent / 'erros.txt'
        with caminho.open('w', encoding='utf-8') as f:
            f.write(f"Clientes: {', '.join(clientes)}\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Diretório: {diretorio}\n")
            f.write('=' * 60 + '\n\n')

            if erros:
                for erro in erros:
                    f.write(f"{erro}\n")
            else:
                f.write("Nenhum erro crítico encontrado.\n")

    def processar_lote(self, diretorio: Path, clientes: List[str], scripts: List[ScriptProcessado]):
        self._log('info', f"Executando {len(scripts)} script(s) em {len(clientes)} cliente(s)")

        versoes = {}
        for cliente in clientes:
            versao = self._buscar_versao_cliente(cliente)
            versoes[cliente] = versao
            if versao:
                self._log('info', f"{cliente}: Última versão no banco — {versao}")

        total_operacoes = sum(
            len([s for s in scripts if s.nome_arquivo > (versoes[c] or '')])
            for c in clientes
        )
        operacao_atual = 0
        resultados_execucao = {}
        erros_criticos: List[str] = []
        ultimo_script_por_cliente = {cliente: None for cliente in clientes}

        for script in scripts:
            resultados_script = {}

            for cliente in clientes:
                if script.nome_arquivo <= (versoes.get(cliente) or ''):
                    continue

                operacao_atual += 1
                self._progresso(operacao_atual, total_operacoes, f"{script.nome_arquivo} -> {cliente}")
                resultado = self.executar_script_em_cliente(script, cliente)
                resultados_script[cliente] = resultado
                ultimo_script_por_cliente[cliente] = script.nome_arquivo

                if not resultado.sucesso and not self._is_ignorable(resultado.mensagem):
                    erros_criticos.append(f"[{cliente}] {script.nome_arquivo}: {resultado.mensagem}")

            if resultados_script:
                resultados_execucao[script.nome_arquivo] = resultados_script

        for cliente, ultimo_script in ultimo_script_por_cliente.items():
            if ultimo_script:
                self._atualizar_versao_cliente(cliente, ultimo_script)

        self._gravar_erros(diretorio, clientes, erros_criticos)

        return resultados_execucao