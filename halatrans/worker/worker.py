import logging
from concurrent.futures import Future, ProcessPoolExecutor
from multiprocessing.managers import SyncManager, ValueProxy
from typing import Tuple, Type, TypeVar

from halatrans.services.interface import BaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseService)


def process_worker(cls: Type[T], task_id: str, stop_flag: ValueProxy[int], *args):
    logger.info(f"[Task: {task_id}] Worker start, cls: {cls}")
    # logger.info(f"All parametes: {args}")
    try:
        cls.process_worker(stop_flag, *args)
    except Exception as err:
        logger.error(err)
    logger.info(f"[Task: {task_id}] Worker end, {cls}")


def launch_process(
    executor: ProcessPoolExecutor,
    manager: SyncManager,
    cls: Type[T],
    task_id: str,
    *args,
) -> Tuple[Future, ValueProxy[int]]:
    stop_flag = manager.Value("i", 0)
    future = executor.submit(process_worker, cls, task_id, stop_flag, *args)
    return (future, stop_flag)
