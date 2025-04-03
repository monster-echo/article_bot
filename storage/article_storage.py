from datetime import datetime
import json
import os
from typing import Set
import uuid
import logging
import requests
from config import AISTUDIOX_API_URL
from urllib.parse import urljoin


class ArticleStorage:
    def __init__(self):
        self.links_cache: Set[str] = set()
        self.logger = logging.getLogger(self.__class__.__name__)

        self._load_existing_links()

    def _load_existing_links(self):
        """加载已存在的文章链接"""

        # 从文件系统加载
        response = requests.get(
            urljoin(
                AISTUDIOX_API_URL,
                f"api/posts?startTime={datetime.now().date().isoformat()}&pageSize=10000",
            )
        )

        response.raise_for_status()
        data = response.json()
        posts = data.get("posts", [])
        # 从 posts 中提取链接
        self.links_cache = set(post.get("link") for post in posts if post.get("link"))
        self.logger.info(
            f"Loaded {len(self.links_cache)} existing links. Total posts: {data.get('total', 0)}"
        )

    def save_article(self, article) -> bool:
        """保存文章，如果链接已存在返回False"""
        if article.link in self.links_cache:
            return False

        article_dict = article.dict()
        article_dict["published"] = article_dict["published"].isoformat()

        response = requests.post(
            urljoin(AISTUDIOX_API_URL, "api/posts"), json=article_dict
        )
        response.raise_for_status()
        data = response.json()
        # 检查返回结果是否成功（根据实际API响应格式调整）
        if not data.get("link"):
            self.logger.error(f"Failed to save article: No posts returned in response")
            return False

        # 更新缓存
        self.links_cache.add(article.link)
        return True
