from abc import ABC, abstractmethod


class Bot(ABC):
    @abstractmethod
    def get_response(self, prompt: str) -> str:
        pass
