import asyncio
import logging
import queue
import threading
from dataclasses import dataclass
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import zmq

from halatrans.services.base_service import BaseService, ServiceConfig
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
    whisper_pub_addr: str
    translation_pub_addr: str
    assistant_pub_addr: str


class RTS2TService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.__output_queue__ = queue.Queue(maxsize=OUTPUT_QUEUE_SIZE_LIMIT)
        self.__output_msg_thread__: Optional[threading.Thread] = None

    def __init_output_msg_thread__(self, stop_flag: ValueProxy[int]):
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
        logger.info("RTS2TService output msg thread start.")
        ctx = zmq.Context()
        try:
            output_sub = create_sub_socket(
                ctx, config.output_pub_addr, [config.output_pub_topic]
            )

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
            ctx.term()
        logger.info("RTS2TService output msg thread end.")

    @staticmethod
    async def __thread_main__(
        output_queue: queue.Queue, config: RTS2TServiceParameters
    ):
        task = asyncio.create_task(
            RTS2TService.__thread_task_handler__(output_queue, config)
        )
        await asyncio.gather(task)

    def __output_msg_thread_func__(
        self, output_queue: queue.Queue, config: RTS2TServiceParameters
    ):
        asyncio.run(RTS2TService.__thread_main__(output_queue, config))

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
            ctx, config.transcribe_pub_addr, ["transcribe"]
        )
        whisper_sub = create_sub_socket(ctx, config.whisper_pub_addr, ["transcribe"])
        translation_sub = create_sub_socket(
            ctx, config.translation_pub_addr, ["translation"]
        )
        assistant_sub = create_sub_socket(ctx, config.assistant_pub_addr, ["assistant"])

        def should_stop() -> bool:
            if stop_flag.get() != 0:
                return True
            return False

        def message_handler(sock: zmq.Socket, chunks: List[bytes]):
            nonlocal output_pub
            for chunk in chunks:
                output_pub.send_multipart([b"rts2t", chunk])

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

        logger.info("RTS2TService worker end.")
