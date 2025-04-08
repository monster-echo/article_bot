from common_jobs.base import CommonJobBase
import requests

from wechat_publisher import publish_article
from config import AISTUDIOX_API_URL

SYSTEM_PROMPT = """
下面内容是一篇新闻稿，现在需要你为我起一个能提高点击率的标题

{content}

请你只返回标题，不要返回其他任何内容
"""

PEXEL_SYSTEM_PROMPT = """

需要你为我生成2,3个图片搜索的关键词，要求是英文的，用于 pexels 搜索图片
请你只返回关键词，不要返回其他任何内容

{content}

"""


class WechatJob(CommonJobBase):
    """
    Wechat job class.
    """

    interval = 60 * 5  # 5 minutes

    def run(self):
        """
        Run the Wechat job.
        """
        get_pending_posts_url = f"{AISTUDIOX_API_URL}/api/posts?wechatStatus=pending"
        response = requests.get(get_pending_posts_url)
        response.raise_for_status()

        data = response.json()
        if not data["posts"]:
            self.logger.info("No new articles found.")
            return

        self.logger.info(f"发现 {len(data['posts'])} 篇新文章")

        for post in data["posts"]:
            self.publish(post)

    def publish(self, post):
        title = post["title"]
        markdown_content = post["content"]
        content = post["wechatPublish"]["content"]
        author = "echo072"
        thumb_url = post["mediaFiles"][0] if len(post["mediaFiles"]) > 0 else None

        if not title:
            title = self.llm.invoke(
                SYSTEM_PROMPT.format(content=markdown_content),
            ).content

            # 删除 title 开头和末尾的 ' 或 "
            title = title.strip().strip("'\"")

        if not thumb_url:
            #  从 pexels 获取一张随机图片
            query = self.llm.invoke(
                PEXEL_SYSTEM_PROMPT.format(content=title),
            ).content

            pexels_api_url = "https://api.pexels.com/v1/search"
            headers = {
                "Authorization": "563492ad6f91700001000001f6261981c82c43daa0f0098107766e66"
            }
            response = requests.get(
                pexels_api_url,
                headers=headers,
                params={"query": query, "per_page": 1},
            )
            response.raise_for_status()
            thumb_url = (
                response.json()["photos"][0]["src"]["original"]
                if response.json()["photos"]
                else None
            )

        try:
            result = publish_article(title, content, author, thumb_url=thumb_url)
            self.logger.info(f"文章 {title} 发布成功")
            put_posts_url = f"{AISTUDIOX_API_URL}/api/posts"

            json = {
                "id": post["id"],
                "wechatPublish": {
                    "status": "PUBLISHED",
                    "mediaId": result["media_id"],
                    "publishId": str(result["publish_id"]),
                },
            }

            if not post["title"]:
                json["title"] = title
            if not post["mediaFiles"]:
                json["mediaFiles"] = [
                    thumb_url,
                ]

            if result["success"]:
                response = requests.put(
                    put_posts_url,
                    json=json,
                )
                response.raise_for_status()
                self.logger.info(f"文章 {title} 更新状态成功")
            else:
                self.logger.error(f"文章 {title} 发布失败: {result['error']}")
                put_posts_url = f"{AISTUDIOX_API_URL}/api/posts"
                response = requests.put(
                    put_posts_url,
                    json={
                        "id": post["id"],
                        "wechatPublish": {
                            "status": "FAILED",
                            "error": result["error"],
                        },
                    },
                )
                response.raise_for_status()
                self.logger.info(f"文章 {title} 更新状态失败")
        except Exception as e:
            self.logger.error(f"文章 {title} 发布失败: {e}")
            put_posts_url = f"{AISTUDIOX_API_URL}/api/posts"
            response = requests.put(
                put_posts_url,
                json={
                    "id": post["id"],
                    "wechatPublish": {
                        "status": "FAILED",
                        "error": str(e),
                    },
                },
            )
            response.raise_for_status()
            self.logger.info(f"文章 {title} 更新状态失败")
