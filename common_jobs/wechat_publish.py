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


def get_pending_posts():
    """
    获取待发布的文章列表
    """
    get_pending_posts_url = (
        f"{AISTUDIOX_API_URL}/api/posts?wechatStatus=pending&includeWechatPublish=true"
    )
    response = requests.get(get_pending_posts_url)
    response.raise_for_status()
    data = response.json()
    return data["items"] if data["items"] else None


class WechatJob(CommonJobBase):
    """
    Wechat job class.
    """

    interval = 60 * 5  # 5 minutes

    async def run(self):
        """
        Run the Wechat job.
        """
        posts = get_pending_posts()
        if not posts:
            self.logger.info("No new articles found.")
            return
        self.logger.info(f"发现 {len(posts)} 篇新文章")

        for post in posts:
            self.publish(post)

    def publish(self, post):
        id = post["id"]
        self.logger.info(f"开始发布文章 {id}")
        title = post["translations"][0]["title"]
        content = post["wechatPublish"]["content"]
        author = "echo072"
        thumb_url = (
            post["translations"][0]["mediaFiles"][0]
            if len(post["translations"][0]["mediaFiles"]) > 0
            else post["translations"][0]["cover"]
        )

        if not title:
            title = self.llm.invoke(
                SYSTEM_PROMPT.format(content=content),
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
        else:
            # 直接使用已有的图片
            thumb_url = f"{AISTUDIOX_API_URL}/api/oss?ossKey={thumb_url}"

        put_posts_url = f"{AISTUDIOX_API_URL}/api/posts/{id}"
        try:
            result = publish_article(title, content, author, thumb_url=thumb_url)
            if not result["success"]:
                raise Exception(result["error"])
            json = {
                "id": post["id"],
                "wechatPublish": {
                    "status": "PUBLISHED",
                    "mediaId": result["media_id"],
                    "publishId": str(result["publish_id"]),
                },
            }

            if result["success"]:
                response = requests.put(
                    put_posts_url,
                    json=json,
                )
                response.raise_for_status()
                self.logger.info(f"文章 {title} 更新状态成功")
            else:
                self.logger.error(f"文章 {title} 发布失败: {result['error']}")
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
