import logging
import queue
import signal
from typing import Any, Dict, List, Optional

from halatrans.services.base_service import BaseService
from halatrans.services.process_task_manager import (ProcessTaskManager,
                                                     ServiceState,
                                                     ServiceTaskIdDict)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseServiceManager:
    def __init__(self):
        self.__task_manager__: Optional[ProcessTaskManager] = None
        self.__service_state__: ServiceState = dict()
        self.__service_task_id_dict__: ServiceTaskIdDict = dict()
        self.is_terminating = False
        self.is_running = False
        self.is_exit = False

        self.__original_sigint_handler__ = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self.__on_handle_sigint__)

    def __on_handle_sigint__(self, signal_num, frame):
        logger.info("on handle sigint!!!")
        self.terminate()
        self.is_exit = True
        if self.__original_sigint_handler__:
            self.__original_sigint_handler__(signal_num, frame)

    def __submit_task__(self, service_name: str, service: BaseService):
        config = service.get_config()
        mode = service.get_mode()
        addr = config.addr
        topic = config.topic
        parameters: Dict[str, Any] = (
            {}
            if service.get_config().parameters is None
            else service.get_config().parameters
        )

        task_id = self.__task_manager__.submit(
            service,
            mode,
            addr,
            topic,
            parameters,
        )
        self.__service_task_id_dict__[service_name] = task_id

    def get_service(self, name: str) -> Optional[BaseService]:
        if name in self.__service_state__:
            return self.__service_state__[name]
        return None

    def start(self) -> str:
        if self.is_running:
            return "services are running."
        if self.is_terminating or self.is_exit:
            return "services are stopping."

        if self.__task_manager__ is None:
            self.__task_manager__ = ProcessTaskManager()

        self.is_running = True

        service_descs = self.on_prepare_start()

        # launch all services
        for k, v in service_descs.items():
            self.__service_state__[k] = v
            self.__submit_task__(k, v)

        self.on_start_finished()

        return "Servcies started."

    def stop(self) -> str:
        if not self.is_running:
            return "Services have not started yet."
        if self.is_terminating or self.is_exit:
            return "Services are stopping."

        self.terminate()

        return "Services stopped."

    def cancel_task_by_name(self, service_name: str):
        if (
            service_name in self.__service_state__
            and service_name in self.__service_task_id_dict__
        ):
            task_id = self.__service_task_id_dict__[service_name]
            service = self.__service_state__.pop(service_name, None)
            self.__task_manager__.cancel_task(task_id)
            self.__service_task_id_dict__.pop(service_name, None)
            if service:
                service.on_terminating()

    def terminate(self):
        self.on_terminate()
        self.is_running = False
        self.is_terminating = True
        if self.__task_manager__:
            self.__task_manager__.terminate()
            self.__task_manager__ = None
        exit_task_services: List[BaseService] = []
        for _, v in self.__service_state__.items():
            exit_task_services.append(v)
        self.__service_state__ = {}
        for service in exit_task_services:
            service.on_terminating()
        self.is_terminating = False

    def on_prepare_start(self) -> ServiceState:
        return {}

    def on_start_finished(self):
        pass

    def on_terminate(self):
        pass
