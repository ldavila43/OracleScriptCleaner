from pathlib import Path
from typing import List
from model import EstatisticasProcessamento, ScriptProcessado
from config import Configuracao
from services import ServicoArquivo, ServicoExecucao


class Controlador:

    def __init__(self):
        self.stats = EstatisticasProcessamento()
        self._tela = None

    def iniciar(self):
        from view.tela import InterfaceGrafica
        self._tela = InterfaceGrafica(self)
        self._tela.executar()

    def iniciar_cli(self, diretorio: Path, credenciais: dict, modo: str, log_erros: Path = None):
        import sys

        def log(tipo, mensagem):
            prefixos = {'info': 'ℹ', 'success': '✓', 'warning': '⚠', 'error': '✗'}
            print(f"{prefixos.get(tipo, '•')}  {mensagem}", flush=True)

        def progresso(atual, total, mensagem):
            print(f"[{atual}/{total}] {mensagem}", flush=True)

        self._log = log
        self._progresso = progresso

        log('info', f"Modo CLI — diretório: {diretorio}")
        log('info', f"Host: {credenciais['host']} | Serviço: {credenciais['service']} | Usuário: {credenciais['user']}")

        scripts, _ = self.processar_lote(
            diretorio=diretorio,
            clientes=['CLI'],
            modo=modo,
            credenciais=credenciais,
            log_erros=log_erros
        )

        stats = self.obter_estatisticas()
        if stats.tem_erros:
            log('warning', f"Concluído com {len(stats.erros)} erro(s). Consulte erros.txt.")
            sys.exit(1)
        else:
            log('success', "Concluído com sucesso!")
            sys.exit(0)

    def _log(self, tipo, mensagem):
        if self._tela:
            self._tela.log(tipo, mensagem)

    def _progresso(self, atual, total, mensagem):
        if self._tela:
            self._tela.atualizar_progresso(atual, total, mensagem)

    def carregar_clientes(self) -> List[str]:
        return Configuracao.carregar_clientes()

    def validar_execucao(self, diretorio, clientes, modo) -> tuple[bool, str]:
        if not diretorio:
            return False, 'Selecione um diretório de scripts primeiro.'

        if modo != 'apenas_processar' and not clientes:
            return False, 'Selecione ao menos um cliente ou escolha "Apenas processar".'

        return True, ''

    def montar_mensagem_confirmacao(self, diretorio, clientes, modo) -> str:
        labels = {
            'atualizar':        'Atualizar (executar scripts posteriores à versão do banco)',
            'executar_todos':   'Executar todos (ignorar versão do banco)',
            'apenas_processar': 'Apenas processar (não executar nos bancos)',
        }

        msg = f'Executar scripts em:\n\nDiretório: {diretorio}\n'
        msg += f'Modo: {labels.get(modo, modo)}\n'

        if modo != 'apenas_processar':
            msg += f'Clientes: {", ".join(clientes)}\n'

        msg += '\nDeseja continuar?'
        return msg

    def processar_lote(self, diretorio: Path, clientes: List[str], modo: str = 'atualizar', credenciais: dict = None, log_erros: Path = None):
        self.stats = EstatisticasProcessamento()
        self.stats.iniciar()

        self._log('info', f"Iniciando processamento em: {diretorio}")
        self._log('info', f"Clientes configurados: {len(clientes)}")

        servico_arquivo = ServicoArquivo(self.stats, self._log)

        try:
            arquivos = servico_arquivo.listar_arquivos_sql(diretorio)
        except ValueError as e:
            self._log('error', str(e))
            return [], {}

        if not arquivos:
            self._log('warning', "Nenhum arquivo .sql encontrado")
            return [], {}

        scripts: List[ScriptProcessado] = []
        total = len(arquivos)

        for idx, arquivo in enumerate(arquivos, 1):
            self._progresso(idx, total, f"Processando {arquivo.name}...")
            script = servico_arquivo.processar_arquivo(arquivo)
            if script:
                scripts.append(script)

        resultados_execucao = {}

        if modo != 'apenas_processar' and clientes and scripts:
            servico_execucao = ServicoExecucao(self.stats, self._log, self._progresso, credenciais=credenciais)
            resultados_execucao = servico_execucao.processar_lote(diretorio, clientes, scripts, modo, log_erros=log_erros)

        self.stats.finalizar()
        self._log('info', f"Processamento concluído em {self.stats.tempo_decorrido:.2f}s")

        return scripts, resultados_execucao

    def obter_estatisticas(self) -> EstatisticasProcessamento:
        return self.stats