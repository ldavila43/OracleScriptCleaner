import oracledb
from config.configuracao import Configuracao
from model.excecoes import ConexaoError


class OracleConnectionManager:
    _thick_mode_ativado = False

    @classmethod
    def inicializar_driver(cls):
        if not cls._thick_mode_ativado:
            try:
                oracledb.init_oracle_client()
                cls._thick_mode_ativado = True
            except Exception as e:
                raise RuntimeError(f"Falha ao carregar Oracle Instant Client: {e}")

    @staticmethod
    def criar_conexao(cliente: str = None, credenciais: dict = None) -> oracledb.Connection:
        if credenciais:
            cfg = credenciais
        else:
            cfg = Configuracao.obter_configuracao_banco(cliente)

        if not all([cfg.get('host'), cfg.get('user'), cfg.get('password'), cfg.get('service')]):
            from model.excecoes import ConfiguracaoError
            campos_faltando = [k for k in ('host', 'user', 'password', 'service') if not cfg.get(k)]
            raise ConfiguracaoError(
                f"Configurações incompletas. Faltando: {', '.join(campos_faltando)}"
            )

        try:
            return oracledb.connect(
                user=cfg['user'],
                password=cfg['password'],
                dsn=f"{cfg['host']}:{cfg.get('port', '1521')}/{cfg['service']}"
            )
        except oracledb.Error as e:
            raise ConexaoError(f"Erro ao conectar: {e}") from e