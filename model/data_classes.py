from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class ResultadoSanitizacao:

    sucesso: bool
    mensagem: str
    conteudo: Optional[str] = None

    def __bool__(self):
        return self.sucesso


@dataclass
class ResultadoExecucao:
    sucesso: bool
    mensagem: str
    linhas_afetadas: int = 0

    def __bool__(self):
        return self.sucesso


@dataclass
class ScriptProcessado:
    nome_arquivo: str
    caminho_completo: Path
    conteudo_original: str
    blocos: List[str]
    charset_origem: str
    foi_convertido: bool
    validado: bool = False
    erro_validacao: Optional[str] = None

    @property
    def tamanho_kb(self) -> float:
        return sum(len(b.encode('utf-8')) for b in self.blocos) / 1024


@dataclass
class EstatisticasProcessamento:

    arquivos_processados: int = 0
    arquivos_convertidos: int = 0
    arquivos_ja_utf8: int = 0
    arquivos_com_erro: int = 0

    scripts_executados: int = 0
    scripts_com_erro: int = 0

    erros: List[str] = field(default_factory=list)

    inicio: Optional[datetime] = None
    fim: Optional[datetime] = None

    def adicionar_erro(self, mensagem: str):
        self.erros.append(mensagem)

    def iniciar(self):
        self.inicio = datetime.now()

    def finalizar(self):
        self.fim = datetime.now()

    @property
    def tempo_decorrido(self) -> Optional[float]:
        if self.inicio and self.fim:
            return (self.fim - self.inicio).total_seconds()
        return None

    @property
    def tem_erros(self) -> bool:
        return self.arquivos_com_erro > 0 or self.scripts_com_erro > 0

    def to_dict(self) -> dict:
        return {
            'arquivos_processados': self.arquivos_processados,
            'arquivos_convertidos': self.arquivos_convertidos,
            'arquivos_ja_utf8': self.arquivos_ja_utf8,
            'arquivos_com_erro': self.arquivos_com_erro,
            'scripts_executados': self.scripts_executados,
            'scripts_com_erro': self.scripts_com_erro,
            'total_erros': len(self.erros),
            'tempo_decorrido': self.tempo_decorrido,
            'tem_erros': self.tem_erros
        }