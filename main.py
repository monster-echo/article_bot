import logging
import logging.handlers
from apscheduler.schedulers.blocking import BlockingScheduler
import os
from common_jobs.base import CommonJobBase
from translations.base import TranslationBase
from utils.jobs import add_jobs

scheduler = BlockingScheduler()


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
        add_jobs(
            scheduler,
            "common_jobs",
            CommonJobBase,
        )

        # 启动调度器
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("新闻采集器退出")
        scheduler.shutdown()
