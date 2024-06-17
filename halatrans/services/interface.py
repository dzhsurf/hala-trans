import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from multiprocessing.managers import ValueProxy
from typing import Any, Callable, Dict, Optional  # noqa: F401

import zmq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the port that was assigned
# addr = socket.getsockopt(zmq.LAST_ENDPOINT).decode("utf-8")
# port = addr.split(":")[-1]


def subscriber_thread(
    pub_addr: str,
    input_queue: queue.Queue,
    output_queue: queue.Queue,
):
    logger.info(f"subscriber thread connect to {pub_addr} ...")

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(pub_addr)
    socket.setsockopt(zmq.SUBSCRIBE, b"")  # all topic

    while True:
        try:
            # TODO: handle input cmd
            cmd = input_queue.get(block=False)
            if cmd == "STOP":
                break
        except queue.Empty:
            pass

        while True:
            try:
                topic, data = socket.recv_multipart(zmq.DONTWAIT)
                output_queue.put(data)
            except zmq.Again:
                break

        time.sleep(0.01)

    socket.close()


@dataclass
class ServiceConfig:
    pub_addr: Optional[str]
    addition: Dict[str, Any]


class BaseService(ABC):
    def __init__(self, config: ServiceConfig) -> None:
        super().__init__()
        self.config = config
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue(maxsize=10000)

        if config.pub_addr:
            self.thread = threading.Thread(
                target=subscriber_thread,
                args=(
                    config.pub_addr,
                    self.input_queue,
                    self.output_queue,
                ),
            )
            self.thread.daemon = True
            self.thread.start()

    def get_config(self) -> ServiceConfig:
        return self.config

    def get_output_queue(self) -> queue.Queue:
        return self.output_queue

    def prepare_process_context(self) -> Any:
        return None

    @staticmethod
    @abstractmethod
    def process_worker(
        stop_flag: ValueProxy[int],
        pub_addr: Optional[str],
        addition: Dict[str, Any],
        *args,
    ):
        pass
