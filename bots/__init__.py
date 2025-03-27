import logging
import pkgutil
import importlib
from datetime import datetime, timedelta
from bots.base import BotBase


def import_submodules():
    """导入 bots 包下的所有模块"""
    package = importlib.import_module("bots")
    for _, name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"bots.{name}")


def add_bots(scheduler, stagger_start=True, initial_delay=0):
    """
    查找并添加所有 BotBase 的子类到调度器

    Args:
        scheduler: APScheduler 调度器实例
        stagger_start: 是否错开启动时间,默认为 True
        initial_delay: 初始延迟时间(分钟),默认为 0
    """
    logger = logging.getLogger(__name__)

    # 确保所有模块都已导入
    import_submodules()

    # 获取所有 BotBase 的子类(排除BotBase)
    def get_all_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_all_subclasses(subclass))
        return subclasses

    bot_classes = [cls for cls in get_all_subclasses(BotBase) if cls not in [BotBase]]

    for idx, bot_class in enumerate(bot_classes):
        try:
            bot = bot_class()
            name = bot_class.__name__.lower().replace("bot", "")

            start_time = datetime.now()
            if stagger_start:
                start_time += timedelta(minutes=initial_delay + idx)
                logger.info(f"调度错开时间 {name}: {start_time}")

            scheduler.add_job(
                func=bot.run,
                trigger="interval",
                seconds=bot.interval,
                next_run_time=start_time,
                id=f"{name}_bot",
                name=f"{name} bot",
                max_instances=1,
                misfire_grace_time=60,
            )
            logger.info(f"Successfully added bot: {name}, next run at {start_time}")

        except Exception as e:
            logger.error(f"Failed to add bot {bot_class.__name__}: {str(e)}")
            continue
