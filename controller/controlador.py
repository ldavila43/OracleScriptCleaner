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

    def _log(self, tipo, mensagem):
        if self._tela:
            self._tela.log(tipo, mensagem)

    def _progresso(self, atual, total, mensagem):
        if self._tela:
            self._tela.atualizar_progresso(atual, total, mensagem)

    def carregar_clientes(self) -> List[str]:
        return Configuracao.carregar_clientes()

    def validar_execucao(self, diretorio, clientes, apenas_processar) -> tuple[bool, str]:
        if not diretorio:
            return False, 'Selecione um diretório de scripts primeiro.'

        if not apenas_processar and not clientes:
            return False, 'Selecione ao menos um cliente ou apenas processe.'

        return True, ''

    def montar_mensagem_confirmacao(self, diretorio, clientes, apenas_processar) -> str:
        msg = f'Executar scripts em:\n\nDiretório: {diretorio}\n'

        if apenas_processar:
            msg += '\nModo: Apenas processar (não executar)\n'
        else:
            msg += f'Clientes: {", ".join(clientes)}\n'

        msg += '\nDeseja continuar?'
        return msg

    def processar_lote(self, diretorio: Path, clientes: List[str], executar: bool = True):
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

        if executar and clientes and scripts:
            servico_execucao = ServicoExecucao(self.stats, self._log, self._progresso)
            resultados_execucao = servico_execucao.processar_lote(diretorio, clientes, scripts)

        self.stats.finalizar()
        self._log('info', f"Processamento concluído em {self.stats.tempo_decorrido:.2f}s")

        return scripts, resultados_execucao

    def obter_estatisticas(self) -> EstatisticasProcessamento:
        return self.stats