from abc import abstractmethod
import logging

from langchain_deepseek import ChatDeepSeek


class CommonJobBase:
    """
    Base class for Common jobs.
    """

    interval = 60 * 5  # 5 minutes

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0,
            max_tokens=4096,
        )

    @abstractmethod
    def run(self):
        raise NotImplementedError("Subclasses must implement this method.")
