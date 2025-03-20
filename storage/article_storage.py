from datetime import datetime
import json
import os
from typing import Set
import uuid


class ArticleStorage:
    def __init__(self, storage_dir: str = "data"):
        self.storage_root_dir = storage_dir
        self.links_cache: Set[str] = set()
        self._load_existing_links()

    def _load_existing_links(self):
        """加载已存在的文章链接"""

        today_dir = os.path.join(
            self.storage_root_dir, datetime.today().strftime("%Y-%m-%d")
        )
        if not os.path.exists(today_dir):
            os.makedirs(today_dir)

        for filename in os.listdir(today_dir):
            if filename.endswith(".json"):
                with open(os.path.join(today_dir, filename), "r") as f:
                    data = json.load(f)
                    self.links_cache.add(data.get("link"))

    def save_article(self, article) -> bool:
        """保存文章，如果链接已存在返回False"""
        if article.link in self.links_cache:
            return False

        today_dir = os.path.join(
            self.storage_root_dir, datetime.today().strftime("%Y-%m-%d")
        )

        filename = f"{article.source}-{uuid.uuid5(uuid.NAMESPACE_URL, article.article_id).hex[:6]}.json"
        filepath = os.path.join(today_dir, filename)

        article_dict = article.dict()
        article_dict["published"] = article_dict["published"].isoformat()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(article_dict, f, ensure_ascii=False, indent=2)

        self.links_cache.add(article.link)
        return True
