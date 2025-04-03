from datetime import datetime
import json
import re
from urllib.parse import urljoin
import requests
from config import AISTUDIOX_API_URL
from prompts.news_transform_prompt import SYSTEM_PROMPT
from transforms.base import TransformBase


class NewsTransform(TransformBase):

    def run(self):
        response = requests.get(
            urljoin(
                AISTUDIOX_API_URL,
                f"api/posts?status=draft&pageSize=10",
            )
        )

        response.raise_for_status()
        data = response.json()
        posts = data.get("posts", [])

        if not posts:
            self.logger.info("没有新文章")
            return []

        for post in posts:
            title = post.get("title")
            content = post.get("content")
            if not content:
                self.logger.info("没有内容")
                continue

            # 提取所有图片src
            img_srcs = re.findall(r'<img[^>]+src="([^"]+)"', content)
            cover_image = img_srcs[0] if img_srcs else ""

            # 提取所有链接href
            source_links = re.findall(r'<a[^>]+href="([^"]+)"', content)

            formatted_content = self.llm.invoke(
                SYSTEM_PROMPT.format(title=title, content=content),
            ).content

            # 分离 <think>... </think> 的内容
            if "<think>" in formatted_content and "</think>" in formatted_content:
                start_index = formatted_content.index("<think>") + len("<think>")
                end_index = formatted_content.index("</think>")
                think_content = formatted_content[start_index:end_index]

                self.logger.info(f"Thinking: {think_content}")

                # 从 </think> 后面获取 formatted_content 内容
                formatted_content = formatted_content[end_index + len("</think>") :]
                self.logger.info(f"formatted content: {formatted_content}")
            else:
                self.logger.info("没有 <think> 标签的内容")

            # 处理返回的 JSON 数据
            try:
                ## 字符串里面可能包含 除了json外其他的字符串，用正则获取最大的json
                json_pattern = r"(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\})"
                json_matches = re.findall(json_pattern, formatted_content)

                if json_matches:
                    # Find the largest JSON string by length
                    largest_json = max(json_matches, key=len)
                    formatted_content = largest_json
                else:
                    self.logger.error("没有找到有效的JSON内容")
                    continue

                formatted_content = json.loads(formatted_content)

                formatted_content["cover_image"] = cover_image
                formatted_content["source_links"] = source_links

            except json.JSONDecodeError as e:
                self.logger.error(f"JSON 解析错误: {e}")
                continue

            isAd = formatted_content.get("is_ad", False)
            if isAd:
                response = requests.put(
                    urljoin(
                        AISTUDIOX_API_URL,
                        f"api/posts",
                    ),
                    json={
                        "id": post.get("id"),
                        "status": "rejected",
                    },
                )
                self.logger.info(f"文章 {post.get('id')} 被拒绝")
            else:
                response = requests.put(
                    urljoin(
                        AISTUDIOX_API_URL,
                        f"api/posts",
                    ),
                    json={
                        "id": post.get("id"),
                        "formattedTitle": formatted_content.get("title"),
                        "formattedContent": formatted_content.get("content"),
                        "keywords": formatted_content.get("keywords"),
                        "tags": formatted_content.get("tags"),
                        "coverImage": formatted_content.get("cover_image"),
                        "sourceUrls": formatted_content.get("source_links"),
                        "status": "pending",
                    },
                )
                self.logger.info(f"文章 {post.get('id')} 已经处理")

            response.raise_for_status()
            self.logger.info(f"文章 {post.get('id')} 处理完成")
