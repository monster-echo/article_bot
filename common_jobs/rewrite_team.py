import json
import os
from typing import AsyncIterator, List
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool
from autogen_core import TRACE_LOGGER_NAME
import logging
import requests
import os
import time
from bs4 import BeautifulSoup
from config import EDGE_AISHUOHUA_URL, SEARXNG_API_URL
import yaml

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

    enriched_results = []
    for item in results[:num_results]:
        if not item.get("url"):
            continue
        body = crawl_page(item["url"], max_chars)
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


def crawl_page(url: str, max_chars: int = 500):
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

        logger.info(f"crawl_page 获取到页面内容: {content}")
        return content.strip()
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        logger.error(f"Error fetching {url}: {str(e)}")
        return ""


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

crawl_page_tool = FunctionTool(
    crawl_page,
    description="Crawl a web page and return its content",
)

cover_image_tool = FunctionTool(
    cover_image,
    description="Generate a cover image for the news article",
)


class RewriteTeam:
    """
    RewriteTeam tasked with rewriting the article.
    """

    def __init__(self, config_path="config/agents.yaml"):
        self.config = self._load_config(config_path)
        self.model = self._init_model()
        self.agents = self._create_agents()
        self.team = self._create_team()

    def _load_config(self, config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _init_model(self):
        """
        Initialize the model for rewriting.
        """
        # Placeholder for model initialization logic
        return OpenAIChatCompletionClient(
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

    def _create_agents(self) -> List[AssistantAgent]:
        agents = []

        agents.append(
            AssistantAgent(
                name="keywords_agent",
                model_client=self.model,
                description="A helpful assistant that can extract keywords from news articles.",
                system_message=self.config["keywords_agent"]["system_message"],
            )
        )
        agents.append(
            AssistantAgent(
                name="cover_agent",
                model_client=self.model,
                description="A helpful assistant that can choose a cover or generate a cover image for the news article.",
                system_message=self.config["cover_agent"]["system_message"],
                tools=[cover_image_tool],
            )
        )
        agents.append(
            AssistantAgent(
                name="search_agent",
                model_client=self.model,
                description="A web search agent.",
                tools=[google_search_tool, crawl_page_tool],
                system_message=self.config["search_agent"]["system_message"],
            )
        )
        agents.append(
            AssistantAgent(
                name="group_agent",
                model_client=self.model,
                description="A helpful assistant that can group the news article into categories.",
                system_message=self.config["group_agent"]["system_message"],
            )
        )
        agents.append(
            AssistantAgent(
                name="summary_agent",
                model_client=self.model,
                description="A helpful assistant that can summarize the news article.",
                system_message=self.config["summary_agent"]["system_message"],
            )
        )
        agents.append(
            AssistantAgent(
                name="report_agent",
                model_client=self.model,
                description="A helpful assistant that can generate a report based on the news article.",
                system_message=self.config["report_agent"]["system_message"],
            )
        )
        return agents

    def _create_team(self) -> RoundRobinGroupChat:

        termination = TextMentionTermination("TERMINATE")

        return RoundRobinGroupChat(
            self.agents,
            termination_condition=termination,
        )

    def reset(self):
        """
        Reset the team.
        """
        self.team.reset()

    def rewrite(self, article) -> AsyncIterator:
        """
        Rewrite the article using the team.
        """
        return self.team.run_stream(task=json.dumps(article, ensure_ascii=False))
