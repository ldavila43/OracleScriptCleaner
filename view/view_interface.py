from abc import ABC, abstractmethod

class ViewInterface(ABC):

    @abstractmethod
    def log(self, tipo: str, mensagem: str):
        pass

    @abstractmethod
    def atualizar_progresso(self, atual: int, total: int, mensagem: str):
        pass