import re
from pathlib import Path
from typing import List, Optional
from model import sanitizar, ScriptProcessado, EstatisticasProcessamento

_TIPOS_VIEW = ('CREATE OR REPLACE VIEW', 'CREATE VIEW')

_SQLPLUS_IGNORAR = re.compile(
    r'^\s*('
    r'set\s+define\s+\w+'
    r'|set\s+serveroutput\s+\w+'
    r'|set\s+feedback\s+\w+'
    r'|set\s+echo\s+\w+'
    r'|set\s+verify\s+\w+'
    r'|set\s+heading\s+\w+'
    r'|set\s+pagesize\s+\w+'
    r'|set\s+linesize\s+\w+'
    r'|set\s+timing\s+\w+'
    r'|set\s+trimspool\s+\w+'
    r'|spool\s+.*'
    r'|show\s+.*'
    r'|exit'
    r'|quit'
    r'|connect\s+(?!by\b)\S+'
    r'|conn\s+.*'
    r'|prompt\s+.*'
    r'|pause\s+.*'
    r'|host\s+.*'
    r'|whenever\s+.*'
    r')\s*;?\s*$',
    re.IGNORECASE
)

_BLOCOS_INDIVISIVEIS = (
    'CREATE OR REPLACE PROCEDURE',
    'CREATE OR REPLACE FUNCTION',
    'CREATE OR REPLACE PACKAGE',
    'CREATE OR REPLACE TRIGGER',
    'CREATE OR REPLACE TYPE',
    'CREATE OR REPLACE VIEW',
    'CREATE VIEW',
    'CREATE PROCEDURE',
    'CREATE FUNCTION',
    'CREATE PACKAGE',
    'CREATE TRIGGER',
    'CREATE TYPE',
    'BEGIN',
    'DECLARE',
)


class ServicoArquivo:

    def __init__(self, stats: EstatisticasProcessamento, log_fn):
        self.stats = stats
        self._log = log_fn

    def listar_arquivos_sql(self, diretorio: Path) -> List[Path]:
        if not diretorio.exists():
            raise ValueError(f"Diretório não encontrado: {diretorio}")

        if not diretorio.is_dir():
            raise ValueError(f"Caminho não é um diretório: {diretorio}")

        arquivos = sorted(diretorio.glob("*.sql"))
        self._log('info', f"Encontrados {len(arquivos)} arquivo(s) em {diretorio}")
        return arquivos

    def limpar_script(self, conteudo: str) -> List[str]:
        linhas = conteudo.split('\n')
        bloco_atual = []
        blocos = []
        em_comentario_bloco = False

        for linha in linhas:
            linha_strip = linha.strip()

            if _SQLPLUS_IGNORAR.match(linha_strip):
                continue

            if '/*' in linha_strip:
                em_comentario_bloco = True

            if em_comentario_bloco:
                if bloco_atual:
                    bloco_atual.append(linha)
                if '*/' in linha_strip:
                    em_comentario_bloco = False
                continue

            if '--' in linha_strip:
                if bloco_atual:
                    bloco_atual.append(linha)
                    continue
                else:
                    idx_comentario = linha.index('--')
                    linha = linha[:idx_comentario].rstrip()
                    linha_strip = linha.strip()

            if linha_strip == '/':
                bloco = '\n'.join(bloco_atual).strip()
                if bloco:
                    blocos.extend(self._dividir_bloco_se_necessario(bloco))
                bloco_atual = []
            elif linha_strip:
                bloco_atual.append(linha)
            elif bloco_atual:
                bloco_atual.append(' ')

        bloco_final = '\n'.join(bloco_atual).strip()
        if bloco_final:
            blocos.extend(self._dividir_bloco_se_necessario(bloco_final))

        return blocos

    def _dividir_bloco_se_necessario(self, bloco: str) -> List[str]:
        bloco_upper = bloco.upper().lstrip()

        eh_indivisivel = any(bloco_upper.startswith(p) for p in _BLOCOS_INDIVISIVEIS)

        if eh_indivisivel:
            if any(bloco_upper.startswith(v) for v in _TIPOS_VIEW):
                return [bloco.rstrip().rstrip(';').rstrip()]
            return [bloco]

        return self._split_por_ponto_virgula_seguro(bloco)

    def _split_por_ponto_virgula_seguro(self, texto: str) -> List[str]:
        partes = []
        atual = []
        i = 0
        n = len(texto)

        while i < n:
            c = texto[i]

            if i + 2 < n and c.lower() == 'q' and texto[i + 1] == "'":
                abertura = texto[i + 2]
                fechamento = {'{': '}', '[': ']', '(': ')', '<': '>'}.get(abertura, abertura)
                atual.append(texto[i:i + 3])
                i += 3
                while i < n:
                    if texto[i] == fechamento and i + 1 < n and texto[i + 1] == "'":
                        atual.append(texto[i:i + 2])
                        i += 2
                        break
                    atual.append(texto[i])
                    i += 1
                continue

            if c == "'":
                atual.append(c)
                i += 1
                while i < n:
                    ch = texto[i]
                    atual.append(ch)
                    i += 1
                    if ch == "'":
                        if i < n and texto[i] == "'":
                            atual.append(texto[i])
                            i += 1
                            continue
                        break
                continue

            if c == ';':
                parte = ''.join(atual).strip()
                if parte:
                    partes.append(parte)
                atual = []
                i += 1
                continue

            atual.append(c)
            i += 1

        parte_final = ''.join(atual).strip()
        if parte_final:
            partes.append(parte_final)

        return partes

    def validar_script(self, conteudo: str) -> tuple[bool, Optional[str]]:
        if not conteudo or not conteudo.strip():
            return False, "Script vazio"

        comandos_permitidos = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE',
            'COMMIT', 'ROLLBACK', 'SAVEPOINT',
            'CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'REPLACE',
            'GRANT', 'REVOKE',
            'DECLARE', 'BEGIN', 'END', 'PROCEDURE', 'FUNCTION',
            'PACKAGE', 'BODY', 'TRIGGER', 'TYPE', 'PRAGMA',
            'IF', 'THEN', 'ELSE', 'ELSIF', 'CASE', 'WHEN',
            'LOOP', 'FOR', 'WHILE', 'EXIT', 'CONTINUE',
            'OPEN', 'FETCH', 'CLOSE', 'BULK', 'COLLECT', 'FORALL',
            'EXCEPTION', 'RAISE', 'EXECUTE', 'IMMEDIATE', 'PIPE',
            'PIPELINED', 'INTO', 'COMMENT'
        ]

        padrao = re.compile(r'\b(' + '|'.join(comandos_permitidos) + r')\b', re.IGNORECASE)
        conteudo_limpo = re.sub(r'--.*', '', conteudo)

        if not padrao.search(conteudo_limpo):
            return False, "Nenhum comando SQL/PLSQL válido encontrado"

        return True, None

    def processar_arquivo(self, arquivo: Path) -> Optional[ScriptProcessado]:
        self.stats.arquivos_processados += 1

        try:
            self._log('info', f"Processando: {arquivo.name}")
            resultado = sanitizar(arquivo)

            if not resultado.sucesso:
                self._log('error', f"{arquivo.name} - {resultado.mensagem}")
                self.stats.arquivos_com_erro += 1
                self.stats.adicionar_erro(f"{arquivo.name}: {resultado.mensagem}")
                return None

            foi_convertido = resultado.mensagem.startswith('convertido-de-')

            if foi_convertido:
                self.stats.arquivos_convertidos += 1
                self._log('success', f"{arquivo.name} - Convertido de {resultado.mensagem}")
            else:
                self.stats.arquivos_ja_utf8 += 1
                self._log('info', f"{arquivo.name} - Já em UTF-8")

            blocos = self.limpar_script(resultado.conteudo)
            valido, erro_validacao = self.validar_script('\n'.join(blocos))

            return ScriptProcessado(
                nome_arquivo=arquivo.name,
                caminho_completo=arquivo,
                conteudo_original=resultado.conteudo,
                blocos=blocos,
                charset_origem=resultado.mensagem,
                foi_convertido=foi_convertido,
                validado=valido,
                erro_validacao=erro_validacao
            )

        except Exception as e:
            self._log('error', f"{arquivo.name} - Exceção: {str(e)}")
            self.stats.arquivos_com_erro += 1
            self.stats.adicionar_erro(f"{arquivo.name}: Exceção - {str(e)}")
            return None