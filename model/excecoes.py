class SqlExecutorError(Exception):
    pass


class ConexaoError(SqlExecutorError):
    pass


class ConfiguracaoError(SqlExecutorError):
    pass


class ExecucaoError(SqlExecutorError):

    def __init__(self, mensagem: str, codigo_ora: str = None):
        super().__init__(mensagem)
        self.codigo_ora = codigo_ora

    @classmethod
    def from_oracle_error(cls, erro: str) -> 'ExecucaoError':
        """Fabrica a exceção correta baseado no código ORA."""
        import re
        match = re.search(r'ORA-(\d+)', erro)
        codigo = f'ORA-{match.group(1)}' if match else None

        codigos_sintaxe = {'ORA-00900', 'ORA-06550', 'ORA-00907', 'ORA-00904'}
        codigos_objeto  = {'ORA-00942', 'ORA-04043', 'ORA-00955'}
        codigos_permissao = {'ORA-01031', 'ORA-00942'}

        if codigo in codigos_sintaxe:
            return SintaxeError(erro, codigo)
        if codigo in codigos_objeto:
            return ObjetoError(erro, codigo)
        if codigo in codigos_permissao:
            return PermissaoError(erro, codigo)

        return cls(erro, codigo)


class SintaxeError(ExecucaoError):
    pass


class ObjetoError(ExecucaoError):
    pass


class PermissaoError(ExecucaoError):
    pass


class ArquivoError(SqlExecutorError):
    pass