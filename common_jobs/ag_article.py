import json
import os
import re
from autogen_core import TRACE_LOGGER_NAME
import logging
import requests
import os
from common_jobs.base import CommonJobBase
from common_jobs.rewrite_team import RewriteTeam
from config import AISTUDIOX_API_URL


logger = logging.getLogger(TRACE_LOGGER_NAME)


async def ag_format_article(team_stream):

    async for message in team_stream:
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
    authors = os.getenv(
        "ARTICLE_FILTER_AUTHORS",
        "",
    )

    get_drafts_url = f"{AISTUDIOX_API_URL}/api/drafts?authors={authors}"
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
    interval = 60 * 1  # 1 minutes

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
                rewrite_team = RewriteTeam()
                team_stream = rewrite_team.rewrite(content)
                article = await ag_format_article(team_stream)
                rewrite_article(id, article)
                self.logger.info(f"文章 {id} 重写成功.")
            except Exception as e:
                self.logger.error(f"重写文章失败 {id}:  {e}")
                remove_draft(id)
