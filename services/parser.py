import re
from typing import List


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


class ParserSql:

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

        if any(bloco_upper.startswith(p) for p in _BLOCOS_INDIVISIVEIS):
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