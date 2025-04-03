from abc import abstractmethod
import logging
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama
import requests


class TransformBase:
    interval = 60

    def __init__(self):

        self.logger = logging.getLogger(self.__class__.__name__)
        # self.llm = ChatOllama(
        #     model="qwq",
        #     temperature=0.2,
        #     max_tokens=4096,
        # )
        self.llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0,
            max_tokens=4096,
        )

    @abstractmethod
    def run(self):
        raise NotImplementedError("Subclasses must implement this method.")
