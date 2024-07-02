import asyncio
import logging
import signal
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, Generator, List, Optional, Type, TypeVar

import zmq

from halatrans.services.utils import (
    create_pub_socket,
    create_rep_socket,
    create_req_socket,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceMode(Enum):
    CUSTOM = 0
    REQREP = 1
    PUBSUB = 2


@dataclass
class ServiceConfig:
    addr: Optional[str] = None  # Only available when mode is [REQREP | PUBSUB]
    topic: Optional[str] = None  # Only available when mode is PUBSUB
    parameters: Dict[str, Any] = None


# Get the port that was assigned
# addr = socket.getsockopt(zmq.LAST_ENDPOINT).decode("utf-8")
# port = addr.split(":")[-1]

ServiceT = TypeVar("ServiceT", bound="BaseService")


class BaseService(ABC):
    def __init__(self, config: ServiceConfig):
        super().__init__()
        self.config = config

    def get_config(self) -> ServiceConfig:
        return self.config

    @abstractmethod
    def get_mode(self) -> ServiceMode:
        pass

    @abstractmethod
    def on_worker_process_launched(self, stop_flag: ValueProxy[int]):
        pass

    @abstractmethod
    def on_terminating(self):
        pass

    @staticmethod
    @abstractmethod
    async def on_worker_process_begin(
        stop_flag: ValueProxy[int],
        cls: Type[ServiceT],
        addr: Optional[str],
        topic: Optional[str],
        parameters: Dict[str, Any],
    ):
        pass

    @staticmethod
    def process_worker(
        stop_flag: ValueProxy[int],
        cls: Type[ServiceT],
        mode: ServiceMode,
        addr: Optional[str],
        topic: Optional[str],
        parameters: Dict[str, Any],
    ):
        # setup worker process SIGINT
        original_sigint_handler = signal.getsignal(signal.SIGINT)

        def handle_sigint(signal_num, frame):
            logger.error("handle sigint!!! set stop flag.")
            stop_flag.set(1)
            if original_sigint_handler:
                original_sigint_handler(signal_num, frame)

        signal.signal(signal.SIGINT, handle_sigint)

        # start worker logic
        asyncio.run(
            cls.on_worker_process_begin(stop_flag, cls, addr, topic, parameters)
        )


class BaseServiceImpl(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    def on_worker_process_launched(self, stop_flag: ValueProxy[int]):
        super().on_worker_process_launched(stop_flag)

    def on_terminating(self):
        super().on_terminating()


class RequestResponseService(BaseServiceImpl):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.__init_reqrep_server__()

    def get_mode(self) -> ServiceMode:
        return ServiceMode.REQREP

    async def request(self, input: bytes, timeout: float = 0) -> Optional[bytes]:
        """
        Sends a request to service and waits for a response.

        It sends the input bytes as a multipart message and waits for the response.

        Args:
            input: The input data to be sent as bytes.
            timeout: The maximum time in seconds to wait for a response. Default is 0 (no timeout).

        Returns:
            The response data as bytes, or None if an error occurred or the response is invalid.

        Raises:
            ValueError: If the service mode is not REQREP or the address is not configured.
        """
        if self.config.addr is None:
            raise ValueError(f"Config addr is not setted. {self.config}")

        async def request_task(
            addr: str, bytes_topic: bytes, input: bytes
        ) -> Optional[bytes]:
            # TODO: implement timeout
            ctx = zmq.Context()
            req = create_req_socket(ctx, self.config.addr)
            try:
                req.send_multipart([bytes_topic, input])
                recv_topic, chunk = req.recv_multipart()
                if recv_topic != bytes_topic:
                    raise ValueError(
                        f"Recv topic is not match, s: {bytes_topic}, r: {recv_topic}"
                    )
                return chunk
            except Exception as err:
                logger.error(err)
            finally:
                req.close()
                ctx.term()
            return None

        request_task = asyncio.create_task(
            request_task(self.config.addr, self.unique_topic, input)
        )
        responses: List[Optional[bytes]] = await asyncio.gather(request_task)
        return responses[0]

    def __init_reqrep_server__(self):
        if self.config.addr is None:
            raise ValueError("Config addr is None")

        self.unique_topic = bytes(uuid.uuid4().hex[:8], encoding="utf-8")
        logger.info(f"initial REQREP server, unique topic: {self.unique_topic}")

    @staticmethod
    async def on_worker_process_begin(
        stop_flag: ValueProxy[int],
        cls: Type[ServiceT],
        addr: Optional[str],
        topic: Optional[str],
        parameters: Dict[str, Any],
    ):
        logger.info("REQREP worker start...")
        response_task = asyncio.create_task(
            RequestResponseService.__reqrep_worker_response_handler__(
                stop_flag, cls, addr, parameters
            )
        )
        await asyncio.gather(response_task)
        logger.info("REQREP worker end.")

    @staticmethod
    async def __reqrep_worker_response_handler__(
        stop_flag: ValueProxy[int],
        cls: Type[ServiceT],
        addr: str,
        parameters: Dict[str, Any],
    ):
        ctx = zmq.Context()
        rep_sock = create_rep_socket(ctx, addr)
        poller = zmq.Poller()
        poller.register(rep_sock, zmq.POLLIN)

        while True:
            # detect stop
            if stop_flag.get() != 0:
                break

            socks = dict(poller.poll(1000))  # timeout in milliseconds
            if rep_sock in socks and socks[rep_sock] == zmq.POLLIN:
                try:
                    bytes_topic, chunk = rep_sock.recv_multipart()
                    topic = str(bytes_topic, encoding="utf-8")
                    response_data = cls.on_worker_process_response(
                        parameters, topic, chunk
                    )
                    if response_data:
                        rep_sock.send_multipart([bytes_topic, response_data])
                    else:
                        rep_sock.send_multipart([bytes_topic, b""])
                except Exception as err:
                    logger.error(err)
            else:
                # No message received yet, retrying...
                await asyncio.sleep(0.2)

        poller.unregister(rep_sock)
        rep_sock.close()
        ctx.term()


class PublishSubscribeService(BaseServiceImpl):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.__init_pubsub_server__()

    def get_mode(self) -> ServiceMode:
        return ServiceMode.PUBSUB

    def __init_pubsub_server__(self):
        if self.config.addr is None or self.config.topic is None:
            raise ValueError(f"Config not correct. {self.config}")

        self.unique_topic = bytes(uuid.uuid4().hex[:8], encoding="utf-8")
        logger.info(f"initial PUBSUB server, unique topic: {self.unique_topic}")

    @staticmethod
    async def on_worker_process_begin(
        stop_flag: ValueProxy[int],
        cls: Type[ServiceT],
        addr: Optional[str],
        topic: Optional[str],
        parameters: Dict[str, Any],
    ):
        logger.info("PUBSUB worker start...")
        handler_task = asyncio.create_task(
            PublishSubscribeService.__pubsub_worker_handler__(
                stop_flag, cls, addr, topic, parameters
            )
        )
        await asyncio.gather(handler_task)
        logger.info("PUBSUB worker end.")

    @staticmethod
    async def __pubsub_worker_handler__(
        stop_flag: ValueProxy[int],
        cls: Type[ServiceT],
        addr: str,
        topic: str,
        parameters: Dict[str, Any],
    ):
        ctx = zmq.Context()
        pub_sock = create_pub_socket(ctx, addr)

        gen = cls.on_worker_process_publisher(parameters)
        bytes_topic = bytes(topic, encoding="utf-8")
        while True:
            if stop_flag.get() != 0:
                gen.send("STOP")
                break
            chunk = gen.send(None)
            pub_sock.send_multipart([bytes_topic, chunk])

        pub_sock.close()


class CustomService(BaseServiceImpl):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.__init_custom_server__()

    def get_mode(self) -> ServiceMode:
        return ServiceMode.CUSTOM

    def __init_custom_server__(self):
        pass

    @staticmethod
    async def on_worker_process_begin(
        stop_flag: ValueProxy[int],
        cls: Type[ServiceT],
        addr: Optional[str],
        topic: Optional[str],
        parameters: Dict[str, Any],
    ):
        logger.info("CUSTOM worker start...")
        handler_task = asyncio.create_task(
            CustomService.__custom_worker_handler__(stop_flag, cls, parameters)
        )
        await asyncio.gather(handler_task)
        logger.info("CUSTOM worker end.")

    @staticmethod
    async def __custom_worker_handler__(
        stop_flag: ValueProxy[int],
        cls: Type[ServiceT],
        parameters: Dict[str, Any],
    ):
        cls.on_worker_process_custom(stop_flag, parameters)
