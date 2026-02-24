import os
from pathlib import Path
from dotenv import load_dotenv


class Configuracao:
    _carregado = False

    @classmethod
    def _carregar_env(cls):
        if not cls._carregado:
            dotenv_path = Path(__file__).parent.parent / '.env'
            load_dotenv(dotenv_path)
            cls._carregado = True

    @classmethod
    def carregar_clientes(cls) -> list[str]:
        import json
        clientes_path = Path(__file__).parent.parent / 'clientes.json'

        if not clientes_path.exists():
            return []

        with open(clientes_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def obter_configuracao_banco(cls, cliente: str) -> dict:
        cls._carregar_env()
        return {
            'host': os.getenv(f'{cliente}_HOST'),
            'port': os.getenv('PORT', '1521'),
            'user': os.getenv(f'{cliente}_USER'),
            'password': os.getenv(f'{cliente}_PASSWORD'),
            'service': os.getenv(f'{cliente}_SERVICE'),
        }