from common_jobs.ag_article import AgArticleJob
from common_jobs.telegram_scrape import TelegramScrapeJob
from common_jobs.wechat_publish import WechatJob


job_types = [WechatJob, AgArticleJob, TelegramScrapeJob]
