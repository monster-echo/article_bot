import logging
import pkgutil
import importlib
from datetime import datetime, timedelta
from transforms.base import TransformBase


def import_submodules():
    """导入 transforms 包下的所有模块"""
    package = importlib.import_module("transforms")
    for _, name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"transforms.{name}")


def add_transforms(scheduler, stagger_start=True, initial_delay=0):
    """
    查找并添加所有 TransformBase 的子类到调度器

    Args:
        scheduler: APScheduler 调度器实例
        stagger_start: 是否错开启动时间,默认为 True
        initial_delay: 初始延迟时间(分钟),默认为 0
    """
    logger = logging.getLogger(__name__)

    # 确保所有模块都已导入
    import_submodules()

    # 获取所有 TransformBase 的子类(排除TransformBase)
    def get_all_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_all_subclasses(subclass))
        return subclasses

    classes = [
        cls for cls in get_all_subclasses(TransformBase) if cls not in [TransformBase]
    ]

    for idx, cls in enumerate(classes):
        try:
            transform = cls()
            name = cls.__name__.lower().replace("transform", "")

            start_time = datetime.now()
            if stagger_start:
                start_time += timedelta(minutes=initial_delay + idx)
                logger.info(f"调度错开时间 {name}: {start_time}")

            scheduler.add_job(
                func=transform.run,
                trigger="interval",
                seconds=transform.interval,
                next_run_time=start_time,
                id=f"{name}_transform",
                name=f"{name} transform",
                max_instances=1,
                misfire_grace_time=60,
            )
            logger.info(
                f"Successfully added transform: {name}, next run at {start_time}"
            )

        except Exception as e:
            logger.error(f"Failed to add transform {cls.__name__}: {str(e)}")
            continue
