from typing import Optional
import oracledb
from config.oracle_conection_manager import OracleConnectionManager


class Banco:
    def __init__(self, cliente: str):
        OracleConnectionManager.inicializar_driver()
        self.cliente_nome = cliente
        self.conexao: Optional[oracledb.Connection] = None
        self.cursor: Optional[oracledb.Cursor] = None

    def __enter__(self):
        self.conexao = OracleConnectionManager.criar_conexao(self.cliente_nome)
        self.cursor = self.conexao.cursor()
        return self

    def executar_bloco(self, sql: str) -> int:
        """Executa um único bloco SQL/PLSQL. Retorna linhas afetadas."""
        self.cursor.execute(sql)
        return self.cursor.rowcount

    def executar_query(self, sql: str, **params):
        """Executa uma query e retorna o cursor para iteração."""
        self.cursor.execute(sql, **params)
        return self.cursor

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def commit(self):
        if self.conexao:
            self.conexao.commit()

    def rollback(self):
        if self.conexao:
            self.conexao.rollback()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
        except Exception as e:
            print(f"Aviso: Erro ao fechar cursor: {e}")

        try:
            if self.conexao:
                self.conexao.close()
                self.conexao = None
        except Exception as e:
            print(f"Aviso: Erro ao fechar conexão: {e}")

        return False

    @property
    def esta_conectado(self) -> bool:
        return self.conexao is not None and self.cursor is not None