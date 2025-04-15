import asyncio
import logging
import logging.handlers
import os
from common_jobs.ag_article import AgArticleJob
from common_jobs.base import CommonJobBase
from utils.jobs import add_jobs


def config_logger():
    """
    配置日志记录器
    """
    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    # 设置日志文件名
    file_name = os.path.join(log_dir, "article_job.log")

    # 正确设置日志回滚配置，使用 suffix 参数
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=file_name, when="D", interval=1, backupCount=15, encoding="utf-8"
    )
    # 设置后缀格式为 .YYYYMMDD
    file_handler.namer = lambda name: name.replace(".log.", ".") + ".log"
    file_handler.suffix = "%Y%m%d"

    # 设置日志回滚, 保存在log目录, 一天保存一个文件, 保留15天
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            file_handler,
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


logger = config_logger()

if __name__ == "__main__":
    logger.info("新闻采集器启动")
    try:
        job = AgArticleJob()
        asyncio.run(job.run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("新闻采集器退出")
