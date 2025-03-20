from abc import abstractmethod
import logging
import requests
from pydantic import BaseModel
from storage.article_storage import ArticleStorage
from datetime import datetime
from typing import List, Optional


class Article(BaseModel):
    """文章数据模型"""

    title: str
    link: str
    article_id: str
    published: datetime
    author: str
    description: Optional[str] = None
    categories: List[str] = []
    source: str = ""  # 来源feed名称


class FeedBase:
    url = None
    interval = 60

    def __init__(self):
        if not self.url:
            raise ValueError(f"{self.__class__.__name__} must set url attribute")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.storage = ArticleStorage()

    def fetch_data(self):
        """获取并解析feed数据"""
        self.logger.info("Fetching data from: %s", self.url)
        response = requests.get(self.url)
        response.raise_for_status()
        articles = self.parse_articles(response.text)

        if not articles:
            self.logger.info("没有新文章")
            return []

        self.logger.info("Fetched %d articles", len(articles))

        for article in articles:
            self.save_article(article)

    @abstractmethod
    def parse_articles(self, response_text) -> List[Article]:
        """
        解析文章内容，子类必须实现此方法
        """
        pass

    def save_article(self, article):
        """保存文章"""
        if self.storage.save_article(article):
            self.logger.info("保存文章: %s", article.title)
