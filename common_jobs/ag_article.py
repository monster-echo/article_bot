import asyncio
import json
import os
import re
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool
from autogen_core import TRACE_LOGGER_NAME
import logging
import requests
import os
import time
from bs4 import BeautifulSoup
from common_jobs.base import CommonJobBase
from config import AISTUDIOX_API_URL, EDGE_AISHUOHUA_URL, SEARXNG_API_URL

logger = logging.getLogger(TRACE_LOGGER_NAME)


def google_search(query: str, num_results: int = 2, max_chars: int = 500):

    url = f"{SEARXNG_API_URL}/search"

    print(f"Searching for: {query}")
    params = {
        "q": str(query),
        "format": "json",
    }

    logger.info(f"开始搜索: {query}")
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(response.json())
        logger.error(
            f"API request failed with status code: {response.status_code}, response: {response.text}"
        )
        raise Exception(f"Error in API request: {response.status_code}")

    results = response.json().get("results", [])

    logger.info(f"找到 {len(results)} 个结果")

    def get_page_content(url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            words = text.split()
            content = ""
            for word in words:
                if len(content) + len(word) + 1 > max_chars:
                    break
                content += " " + word
            return content.strip()
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            logger.error(f"Error fetching {url}: {str(e)}")
            return ""

    enriched_results = []
    for item in results[:num_results]:
        if not item.get("url"):
            continue
        body = get_page_content(item["url"])
        logger.info(f"获取到页面内容: {body}")
        enriched_results.append(
            {
                "title": item["title"],
                "url": item["url"],
                "content": item["content"],
                "body": body,
            }
        )
        time.sleep(1)  # Be respectful to the servers

    return enriched_results


def cover_image(prompt: str):
    url = f"{EDGE_AISHUOHUA_URL}/api/comfy?prompt={prompt}"
    logger.info(f"开始生成封面图: {prompt}")
    response = requests.get(url)
    response.raise_for_status()

    image_urls = response.json()
    image_url = image_urls[0]["filePath"]
    return {"cover_prompt": prompt, "cover_url": image_url}


google_search_tool = FunctionTool(
    google_search,
    description="Search Google for information, returns results with a snippet and body content",
)

cover_image_tool = FunctionTool(
    cover_image,
    description="Generate a cover image for the news article",
)


model_client = OpenAIChatCompletionClient(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": "gpt-4o",
        "structured_output": True,
    },
)

keywords_agent = AssistantAgent(
    "keywords_agent",
    model_client=model_client,
    description="A helpful assistant that can extract keywords from news articles.",
    system_message="You are a helpful assistant that can extract relevant keywords from the provided news article to summarize its main points.",
)

cover_agent = AssistantAgent(
    "cover_agent",
    model_client=model_client,
    description="A helpful assistant that can generate a cover image for the news article.",
    system_message="You are a text2Image assistant that can generate image prompts for the news article. "
    "You should provide a detailed prompt for the image generation model to create a cover image for the article."
    "The prompt should be in the format of a single sentence, describing the main theme of the article."
    "The prompt should be in English."
    "Then you should invoke cover_tool to generate the image.",
    tools=[cover_image_tool],
)

search_agent = AssistantAgent(
    "search_agent",
    model_client=model_client,
    tools=[google_search_tool],
    description="A web search agent.",
    system_message="You are a web search agent. Your only tool is search_tool - use it to find information. You make only one search call at a time. Once you have the results, you never do calculations based on them.",
)


group_agent = AssistantAgent(
    "group_agent",
    model_client=model_client,
    description="A helpful assistant that can group the news article into categories.",
    system_message="You are a helpful assistant that can group the news article into categories based on its content. You should provide a list of categories that best describe the article.",
)

summary_agent = AssistantAgent(
    "summary_agent",
    model_client=model_client,
    description="A helpful assistant that can summarize the news article.",
    system_message="You are a helpful assistant that can summarize the news article. You should provide a concise summary of the main points of the article in 200 words or less.",
)

report_agent = AssistantAgent(
    "report_agent",
    model_client=model_client,
    description="A helpful assistant that can generate a report based on the news article.",
    system_message="""You are a helpful assistant that can generate a report based on the news article. 
    You should provide a detailed report of the main points of the article in the following JSON format:
    ```json
    {
        "cn": {
                "title": "string",
                "summary": "string",
                "content": "string"
                "cover_prompt": "string",
                "cover": "string",
                "categories": ["string"],
                "keywords": ["string"],
                "mediaFiles": ["string"],
                "references": [
                    {
                        "caption": "string",
                        "url": "string"
                    }
                ]
            },
        "en": {
            "title": "string",
            "summary": "string",
            "content": "string",
            "cover_prompt": "string",
            "cover": "string",
            "categories": ["string"],
            "keywords": ["string"],
            "mediaFiles": ["string"],
            "references": [
                {
                    "caption": "string",
                    "url": "string"
                }
            ]
        }
    }
    ```

    The `content` should be a detailed summary of the article, including the main points and any relevant information, and should be in the format of markdown.
    Provide the report with all fields populated based on the article content. Ensure the content is accurate and well-structured. 
    When you are done, you must respond with TERMINATE.""",
)


async def ag_format_article(article):
    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat(
        [
            keywords_agent,
            cover_agent,
            search_agent,
            group_agent,
            summary_agent,
            report_agent,
        ],
        termination_condition=termination,
    )

    async for message in team.run_stream(task=json.dumps(article, ensure_ascii=False)):
        logger.info(f"消息来自 {message.source}: {message.content}")
        if message.source == "report_agent":
            logger.info(f"报告内容: {message.content}")
            content = message.content
            regex = r"```json(.*)```"
            match = re.search(regex, content, re.DOTALL)
            if match:
                report_result = match.group(1).strip()
                return json.loads(report_result)

    return None


def get_drafts():
    get_drafts_url = f"{AISTUDIOX_API_URL}/api/drafts?authors=zaihuanews,linuxgram,xhqcankao,AI_Best_Tools,GodlyNews1"
    logger.info(f"开始获取草稿: {get_drafts_url}")
    response = requests.get(get_drafts_url)
    response.raise_for_status()
    data = response.json()
    return data["items"]


def rewrite_article(draft_id, article):
    create_article_url = f"{AISTUDIOX_API_URL}/api/drafts/{draft_id}/rewrite"
    logger.info(f"开始重写文章: {create_article_url}")
    response = requests.post(
        create_article_url,
        json=article,
    )
    response.raise_for_status()
    article = response.json()
    logger.info(f"重写文章成功: {article}")
    return article


def remove_draft(draft_id):
    remove_draft_url = f"{AISTUDIOX_API_URL}/api/drafts/{draft_id}"
    logger.info(f"开始删除草稿: {remove_draft_url}")
    response = requests.delete(remove_draft_url)
    response.raise_for_status()
    logger.info(f"草稿删除成功: {draft_id}")
    return True


class AgArticleJob(CommonJobBase):
    interval = 60 * 5  # 5 minutes

    async def run(self):
        drafts = get_drafts()
        self.logger.info(f"草稿数量: {len(drafts)}")
        if not drafts:
            self.logger.info("没有新草稿.")
            return

        for draft in drafts:
            self.logger.info(f"草稿内容: {draft}")
            id = draft["id"]
            content = draft["data"]
            try:
                article = await ag_format_article(content)
                rewrite_article(id, article)
                self.logger.info(f"文章 {id} 重写成功.")
            except Exception as e:
                self.logger.error(f"重写文章失败 {id}:  {e}")
                remove_draft(id)
