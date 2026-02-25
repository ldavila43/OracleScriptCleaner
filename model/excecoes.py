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

    @property
    def is_ignorable(self) -> bool:
        codigos_informativos = {
            'ORA-00955',  # Nome já usado por um objeto existente
            'ORA-01430',  # Coluna sendo adicionada já existe na tabela
            'ORA-02260',  # Tabela só pode ter uma chave primária
            'ORA-02261',  # Unique/Primary key já existe na tabela
            'ORA-02275',  # Referential constraint já existe
            'ORA-02303',  # Não pode remover/substituir tipo com dependentes
        }
        return self.codigo_ora in codigos_informativos

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