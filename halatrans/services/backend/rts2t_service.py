import asyncio
import logging
import queue
import threading
from dataclasses import dataclass
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import zmq

from halatrans.services.base_service import CustomService, ServiceConfig
from halatrans.services.utils import (create_pub_socket, create_sub_socket,
                                      poll_messages)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_QUEUE_SIZE_LIMIT = 10000


@dataclass
class RTS2TServiceParameters:
    output_pub_addr: str
    output_pub_topic: str
    transcribe_pub_addr: str
    transcribe_pub_partial_topic: str
    whisper_pub_addr: str
    whisper_pub_topic: str
    translation_pub_addr: str
    translation_pub_topic: str
    assistant_pub_addr: str
    assistant_pub_topic: str


class RTS2TService(CustomService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.__output_queue__ = queue.Queue(maxsize=OUTPUT_QUEUE_SIZE_LIMIT)
        self.__output_msg_thread__: Optional[threading.Thread] = None

    def __init_output_msg_thread__(self, stop_flag: ValueProxy[int]):
        if self.__output_msg_thread__ is not None:
            raise ValueError("output msg thread already exist.")

        config = RTS2TServiceParameters(**self.config.parameters)
        self.__output_msg_thread__ = threading.Thread(
            target=self.__output_msg_thread_func__,
            args=(stop_flag, self.__output_queue__, config),
        )
        self.__output_msg_thread__.daemon = True
        self.__output_msg_thread__.start()

    def __wait_for_output_msg_thread_exit__(self):
        if self.__output_msg_thread__ is None:
            return
        self.__output_msg_thread__.join()
        self.__output_msg_thread__ = None

    def get_output_msg_queue(self) -> queue.Queue:
        return self.__output_queue__

    def on_worker_process_launched(self, stop_flag: ValueProxy[int]):
        super().on_worker_process_launched(stop_flag)
        self.__init_output_msg_thread__(stop_flag)

    def on_terminating(self):
        super().on_terminating()
        self.__wait_for_output_msg_thread_exit__()

    @staticmethod
    async def __thread_task_handler__(
        stop_flag: ValueProxy[int],
        output_queue: queue.Queue,
        config: RTS2TServiceParameters,
    ):
        logger.info(f"RTS2TService output msg thread start. {config}")
        ctx = zmq.Context()
        output_sub = create_sub_socket(
            ctx, config.output_pub_addr, [config.output_pub_topic]
        )
        try:

            def should_stop() -> bool:
                if stop_flag.get() != 0:
                    return True
                return False

            def message_handler(sock: zmq.Socket, chunks: List[bytes]):
                for chunk in chunks:
                    output_queue.put(chunk)

            poll_messages([output_sub], message_handler, should_stop)
        except Exception as err:
            logger.error(err)
        finally:
            output_sub.close()
            ctx.term()

        logger.info("RTS2TService output msg thread end.")

    @staticmethod
    async def __thread_main__(
        stop_flag: ValueProxy[int],
        output_queue: queue.Queue,
        config: RTS2TServiceParameters,
    ):
        task = asyncio.create_task(
            RTS2TService.__thread_task_handler__(stop_flag, output_queue, config)
        )
        await asyncio.gather(task)

    def __output_msg_thread_func__(
        self,
        stop_flag: ValueProxy[int],
        output_queue: queue.Queue,
        config: RTS2TServiceParameters,
    ):
        asyncio.run(RTS2TService.__thread_main__(stop_flag, output_queue, config))

    @staticmethod
    def on_worker_process_custom(
        stop_flag: ValueProxy[int], parameters: Dict[str, Any]
    ):
        config = RTS2TServiceParameters(**parameters)
        logger.info(f"RTS2TService worker start. {config}")

        ctx = zmq.Context()

        output_pub = create_pub_socket(ctx, config.output_pub_addr)
        # output_pub.bind("tcp://*:0")
        # Get the port that was assigned
        # addr = socket.getsockopt(zmq.LAST_ENDPOINT).decode("utf-8")
        # port = addr.split(":")[-1]

        transcribe_sub = create_sub_socket(
            ctx, config.transcribe_pub_addr, [config.transcribe_pub_partial_topic]
        )
        whisper_sub = create_sub_socket(
            ctx, config.whisper_pub_addr, [config.whisper_pub_topic]
        )
        translation_sub = create_sub_socket(
            ctx, config.translation_pub_addr, [config.translation_pub_topic]
        )
        assistant_sub = create_sub_socket(
            ctx, config.assistant_pub_addr, [config.assistant_pub_topic]
        )

        def should_stop() -> bool:
            if stop_flag.get() != 0:
                return True
            return False

        bytes_topic = bytes(config.output_pub_topic, encoding="utf-8")

        def message_handler(sock: zmq.Socket, chunks: List[bytes]):
            nonlocal output_pub, bytes_topic
            for chunk in chunks:
                output_pub.send_multipart([bytes_topic, chunk])

        poll_messages(
            [
                transcribe_sub,
                whisper_sub,
                translation_sub,
                assistant_sub,
            ],
            message_handler,
            should_stop,
        )

        # cleanup
        assistant_sub.close()
        transcribe_sub.close()
        whisper_sub.close()
        translation_sub.close()
        output_pub.close()
        ctx.term()

        logger.info("RTS2TService worker end.")
