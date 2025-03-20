import logging
import pkgutil
import importlib
from datetime import datetime, timedelta
from feeds.base import FeedBase
from feeds.telegram_channel_bot import TelegramChannelFeedBase


def import_submodules():
    """导入 feeds 包下的所有模块"""
    package = importlib.import_module("feeds")
    for _, name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"feeds.{name}")


def add_feeds(scheduler, stagger_start=True, initial_delay=0):
    """
    查找并添加所有 FeedBase 的子类到调度器

    Args:
        scheduler: APScheduler 调度器实例
        stagger_start: 是否错开启动时间,默认为 True
        initial_delay: 初始延迟时间(分钟),默认为 0
    """
    logger = logging.getLogger(__name__)

    # 确保所有模块都已导入
    import_submodules()

    # 获取所有 FeedBase 的子类(排除FeedBase和TelegramChannelFeedBase)
    def get_all_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_all_subclasses(subclass))
        return subclasses

    feed_classes = [
        cls
        for cls in get_all_subclasses(FeedBase)
        if cls not in (FeedBase, TelegramChannelFeedBase)
    ]

    for idx, feed_class in enumerate(feed_classes):
        try:
            feed = feed_class()
            name = feed_class.__name__.lower().replace("feed", "")

            start_time = datetime.now()
            if stagger_start:
                start_time += timedelta(minutes=initial_delay + idx)
                logger.info(f"调度错开时间 {name}: {start_time}")

            scheduler.add_job(
                func=feed.fetch_data,
                trigger="interval",
                seconds=feed.interval,
                next_run_time=start_time,
                id=f"fetch_{name}",
                name=f"Fetch {name} news",
                max_instances=1,
                misfire_grace_time=60,
            )
            logger.info(f"Successfully added feed: {name}, next run at {start_time}")

        except Exception as e:
            logger.error(f"Failed to add feed {feed_class.__name__}: {str(e)}")
            continue
