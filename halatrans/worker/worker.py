import logging
from concurrent.futures import Future, ProcessPoolExecutor
from typing import Type, TypeVar

from halatrans.services.interface import BaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseService)


def process_worker(cls: Type[T], task_id: str, *args):
    logger.info(f"[Task: {task_id}] Worker start, cls: {cls}")
    # logger.info(f"All parametes: {args}")
    try:
        cls.process_worker(*args)
    except Exception as err:
        logger.error(err)
    logger.info(f"[Task: {task_id}] Worker end, {cls}")


def launch_process(
    executor: ProcessPoolExecutor, cls: Type[T], task_id: str, *args
) -> Future:
    future = executor.submit(process_worker, cls, task_id, *args)
    return future
