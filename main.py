import sys
from controller import Controlador


def main():
    controlador = Controlador()

    if len(sys.argv) > 1:
        import argparse
        from pathlib import Path

        parser = argparse.ArgumentParser(description='Executor de Scripts SQL — modo CLI')
        parser.add_argument('--usuario',   required=True, help='Usuário do banco')
        parser.add_argument('--senha',     required=True, help='Senha do banco')
        parser.add_argument('--host',      required=True, help='Host do banco Oracle')
        parser.add_argument('--porta',     required=True, help='Porta do banco (padrão: 1521)')
        parser.add_argument('--sid',       required=True, help='SID do banco')
        parser.add_argument('--diretorio', required=True, help='Caminho para o diretório de scripts .sql')
        parser.add_argument('--log-erros',  required=True, help='Caminho do arquivo de log de erros (ex: /tmp/sql_errors.log)')

        args = parser.parse_args()

        credenciais = {
            'host':     args.host,
            'user':     args.usuario,
            'password': args.senha,
            'service':  args.sid,
            'port':     args.porta,
        }

        controlador.iniciar_cli(
            diretorio=Path(args.diretorio),
            credenciais=credenciais,
            modo='atualizar',
            log_erros=Path(args.log_erros)
        )
    else:
        controlador.iniciar()


if __name__ == '__main__':
    main()