import abc


class Processable(abc.ABC):
    @abc.abstractmethod
    def process(self, the_input: str) -> str:
        pass
