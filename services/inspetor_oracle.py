import re
from typing import Optional
from model.banco import Banco


class InspetorOracle:
    _TIPOS_COM_BODY = {'PACKAGE BODY', 'PROCEDURE', 'FUNCTION', 'TRIGGER', 'TYPE'}

    def __init__(self, banco: Banco):
        self._banco = banco

    def extrair_nome_objeto(self, sql: str) -> Optional[tuple[str, str]]:
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

    def verificar_erros_compilacao(self, nome_objeto: str) -> list[str]:
        try:
            self._banco.executar_query(
                """
                SELECT line, position, text
                FROM user_errors
                WHERE name = :nome
                ORDER BY sequence
                """,
                nome=nome_objeto
            )
            rows = self._banco.fetchall()
            return [f"Linha {row[0]}, Col {row[1]}: {row[2].strip()}" for row in rows]
        except Exception:
            return []

    def objeto_invalido(self, nome_objeto: str) -> bool:
        self._banco.executar_query(
            """
            SELECT status FROM user_objects
            WHERE object_name = :nome
            AND status = 'INVALID'
            """,
            nome=nome_objeto
        )
        return self._banco.fetchone() is not None

    def requer_inspecao(self, tipo_objeto: str) -> bool:
        return tipo_objeto in self._TIPOS_COM_BODY