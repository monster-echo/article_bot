from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)


def add_jobs(scheduler, class_types, stagger_start=True, initial_delay=0):
    """
    查找并添加所有 JobBase 的子类到调度器

    Args:
        scheduler: APScheduler 调度器实例
        stagger_start: 是否错开启动时间,默认为 True
        initial_delay: 初始延迟时间(分钟),默认为 0
    """
    logger.info("开始添加任务")
    for idx, _class in enumerate(class_types):
        if hasattr(_class, "interval") and hasattr(_class, "run"):
            add_job(scheduler, _class, stagger_start, initial_delay, idx)
        else:
            logger.warning(f"类 {_class.__name__} 不符合要求，跳过")


def add_job(scheduler, _class, stagger_start, initial_delay, idx):
    """
    添加单个任务到调度器
    Args:
        scheduler: APScheduler 调度器实例
        _class: 任务类
        stagger_start: 是否错开启动时间
        initial_delay: 初始延迟时间(分钟)
        idx: 任务索引
    """

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
