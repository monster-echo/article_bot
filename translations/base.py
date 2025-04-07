from abc import abstractmethod
import logging

from langchain_deepseek import ChatDeepSeek


class TranslationBase:
    """
    Base class for translations.
    """

    interval = 60 * 5  # 5 minutes
    language = "中文"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0,
            max_tokens=4096,
        )

    @abstractmethod
    def run(self):
        """
        Translate the given text to the specified language.
        """
        raise NotImplementedError("Subclasses must implement this method.")
