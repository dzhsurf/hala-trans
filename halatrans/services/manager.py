import concurrent
import concurrent.futures
import logging
import queue
from concurrent.futures import Future, ProcessPoolExecutor
import signal
from typing import Callable, Dict, List, Optional, Tuple  # noqa: F401
from multiprocessing.managers import SyncManager, ValueProxy
import multiprocessing

from halatrans.services.audio_stream_service import AudioStreamService
from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.rts2t_service import RTS2TService
from halatrans.services.transcribe_service import TranscribeService
from halatrans.services.translation_service import TranslationService
from halatrans.services.whisper_service import WhisperService
from halatrans.worker import worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ServiceState = Dict[str, BaseService]
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
        logger.info(f"submit task {task_id}")
        return task_id

    # def cancel_task(self, task_id: str):
    #     if task_id in self.future_dict:
    #         future, stop_flag = self.future_dict.pop(task_id, None)
    #         if future:
    #             stop_flag.set(1)
    #             concurrent.futures.wait([future])

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


class ServiceManager:
    def __init__(self):
        self.task_manager = ProcessTaskManager()
        self.service_state: ServiceState = dict()
        self.is_terminating = False
        self.is_stopping = False
        self.is_running = False
        self.is_exit = False

        signal.signal(signal.SIGINT, self.on_handle_sigint)

    def on_handle_sigint(self, signal_num, frame):
        logger.info("on handle sigint!!!")
        self.terminate()
        self.is_exit = True

    def get_service(self, name: str) -> Optional[BaseService]:
        if name in self.service_state:
            return self.service_state[name]
        return None

    def get_service_msg_queue(self, name: str) -> Optional[queue.Queue]:
        service = self.get_service(name)
        if service:
            return service.get_output_queue()
        return None

    def terminate(self):
        self.is_terminating = True
        self.task_manager.terminate()
        self.is_terminating = False

    def submit_task(self, service: BaseService):
        args = (service.prepare_process_context(),)
        self.task_manager.submit(
            service,
            service.get_config().pub_addr,
            service.get_config().addition,
            *args,
        )

    def start_services(self) -> str:
        if self.is_running:
            return "services are running."
        if self.is_terminating or self.is_exit or self.is_stopping:
            return "services are stopping."

        self.is_running = True

        # describe service component
        def select_config_by_keys(keys: List[str]) -> Dict[str, str]:
            config: Dict[str, str] = {
                "pub_addr": "tcp://localhost:5101",
                "audio_pub_addr": "tcp://localhost:5201",
                "transcribe_pub_addr": "tcp://localhost:5202",
                "whisper_pub_addr": "tcp://localhost:5203",
                "translation_pub_addr": "tcp://localhost:5204",
            }
            copied_dict = {key: config[key] for key in keys if key in config}
            return copied_dict

        service_dict: Dict[str, BaseService] = {
            "rts2t": RTS2TService(
                ServiceConfig(
                    pub_addr="tcp://localhost:5101",
                    addition=select_config_by_keys(
                        [
                            "transcribe_pub_addr",
                            "whisper_pub_addr",
                            "translation_pub_addr",
                        ]
                    ),
                )
            ),
            "rts2t-audio": AudioStreamService(
                ServiceConfig(
                    pub_addr=None,
                    addition=select_config_by_keys(["audio_pub_addr"]),
                )
            ),
            "rts2t-transcribe": TranscribeService(
                ServiceConfig(
                    pub_addr=None,
                    addition=select_config_by_keys(
                        ["audio_pub_addr", "transcribe_pub_addr"]
                    ),
                )
            ),
            "rts2t-whisper": WhisperService(
                ServiceConfig(
                    pub_addr=None,
                    addition=select_config_by_keys(
                        ["transcribe_pub_addr", "whisper_pub_addr"]
                    ),
                )
            ),
            "rts2t-translation": TranslationService(
                ServiceConfig(
                    pub_addr=None,
                    addition=select_config_by_keys(
                        [
                            "transcribe_pub_addr",
                            "whisper_pub_addr",
                            "translation_pub_addr",
                        ]
                    ),
                )
            ),
        }

        # launch all services
        for k, v in service_dict.items():
            self.service_state[k] = v
            self.submit_task(v)

    def stop_services(self) -> str:
        if not self.is_running:
            return "services have not started yet."
        if self.is_terminating or self.is_stopping or self.is_exit:
            return "services are stopping."

        self.is_running = False
        self.is_stopping = True
        self.task_manager.stop_all_tasks()
        self.is_stopping = False

        return "Services stopped."

    def run_command(self, cmd: str) -> str:
        logger.info(f"Run command {cmd}")

        if cmd == "start":
            return self.start_services()
        elif cmd == "stop":
            return self.stop_services()

        return "Unknow command"
