from datetime import datetime, timedelta
import importlib
import logging
import pkgutil
import asyncio


def import_submodules(module):
    """导入 module 包下的所有模块"""
    package = importlib.import_module(module)
    for _, name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{module}.{name}")


def add_jobs(scheduler, module, base_type, stagger_start=True, initial_delay=0):
    """
    查找并添加所有 JobBase 的子类到调度器

    Args:
        scheduler: APScheduler 调度器实例
        stagger_start: 是否错开启动时间,默认为 True
        initial_delay: 初始延迟时间(分钟),默认为 0
    """
    logger = logging.getLogger(__name__)

    # 确保所有模块都已导入
    import_submodules(module)

    # 获取所有 JobBase 的子类(排除JobBase)
    def get_all_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_all_subclasses(subclass))
        return subclasses

    classes = [cls for cls in get_all_subclasses(base_type) if cls not in [base_type]]

    for idx, _class in enumerate(classes):
        try:
            instance = _class()
            name = _class.__name__.lower()

            start_time = datetime.now()
            if stagger_start:
                start_time += timedelta(minutes=initial_delay + idx)
                logger.info(f"调度错开时间 {name}: {start_time}")

            scheduler.add_job(
                func=lambda: asyncio.run(instance.run()),
                trigger="interval",
                seconds=instance.interval,
                next_run_time=start_time,
                id=f"{name}",
                name=f"{name}",
                max_instances=1,
                misfire_grace_time=60,
            )
            logger.info(f"Successfully added job: {name}, next run at {start_time}")

        except Exception as e:
            logger.error(f"Failed to add job {_class.__name__}: {str(e)}")
            continue
