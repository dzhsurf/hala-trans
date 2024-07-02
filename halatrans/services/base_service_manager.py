import logging
import queue
import signal
from typing import Any, Dict, Optional

from halatrans.services.base_service import BaseService
from halatrans.services.process_task_manager import (ProcessTaskManager,
                                                     ServiceState)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseServiceManager:
    def __init__(self):
        self.__task_manager__: Optional[ProcessTaskManager] = None
        self.__service_state__: ServiceState = dict()
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

    def __submit_task__(self, service: BaseService):
        config = service.get_config()
        mode = service.get_mode()
        addr = config.addr
        topic = config.topic
        parameters: Dict[str, Any] = (
            {}
            if service.get_config().parameters is None
            else service.get_config().parameters
        )

        self.__task_manager__.submit(
            service,
            mode,
            addr,
            topic,
            parameters,
        )

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
            self.__submit_task__(v)

        self.on_start_finished()

        return "Servcies started."

    def stop(self) -> str:
        if not self.is_running:
            return "Services have not started yet."
        if self.is_terminating or self.is_exit:
            return "Services are stopping."

        self.terminate()

        return "Services stopped."

    def terminate(self):
        self.on_terminate()
        self.is_running = False
        self.is_terminating = True
        if self.__task_manager__:
            self.__task_manager__.terminate()
            self.__task_manager__ = None
        self.__service_state__ = {}
        self.is_terminating = False

    def on_prepare_start(self) -> ServiceState:
        return {}

    def on_start_finished(self):
        pass

    def on_terminate(self):
        pass
