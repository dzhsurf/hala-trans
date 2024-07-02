import concurrent
import logging
import multiprocessing
from concurrent.futures import Future, ProcessPoolExecutor
from multiprocessing.managers import ValueProxy
from typing import Dict, Tuple

from halatrans.services.base_service import BaseService
from halatrans.worker import worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ServiceState = Dict[str, BaseService]
ServiceTaskIdDict = Dict[str, str]
TaskStateType = Tuple[Future, ValueProxy[int]]


class ProcessTaskManager:
    def __init__(self):
        self.counter = 0
        self.future_dict: Dict[str, TaskStateType] = {}
        self.executor: ProcessPoolExecutor = ProcessPoolExecutor()
        self.manager = multiprocessing.Manager()

    def gen_next_task_id(self) -> str:
        self.counter += 1
        task_id = "task-" + str(self.counter)
        return task_id

    def submit(self, service: BaseService, *args) -> str:
        task_id = self.gen_next_task_id()
        future, stop_flag = worker.launch_process(
            self.executor,
            self.manager,
            service.__class__,
            task_id,
            *args,
        )
        self.future_dict[task_id] = (future, stop_flag)
        service.on_worker_process_launched(stop_flag)
        logger.info(f"submit task {task_id}")
        return task_id

    def cancel_task(self, task_id: str):
        if task_id in self.future_dict:
            logger.info("Canceling task: {task_id}")
            future, stop_flag = self.future_dict.pop(task_id, None)
            if future:
                logger.info("Set stop flag for task and wait for finish. {task_id}")
                stop_flag.set(1)
                concurrent.futures.wait([future])
                logger.info("Task finish. {task_id}")
        else:
            logger.info(f"Task not exist. {task_id}")

    def stop_all_tasks(self):
        futures = []
        for k, v in self.future_dict.items():
            future, stop_flag = v
            if future:
                stop_flag.set(1)
                futures.append(future)
        logger.info(f"Stop all tasks, task count: {len(futures)}")
        self.future_dict = {}
        concurrent.futures.wait(futures)

    def terminate(self):
        self.stop_all_tasks()
        self.executor.shutdown()
        self.manager.shutdown()
        logger.info("terminate finish.")
