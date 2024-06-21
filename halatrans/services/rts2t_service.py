import logging
import signal
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import zmq

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import (create_pub_socket, create_sub_socket,
                                      poll_messages)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RTS2TService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(
        stop_flag: ValueProxy[int],
        pub_addr: Optional[str],
        addition: Dict[str, Any],
        *args,
    ):
        # This is worker process
        logger.info("rts2t worker process start.")

        ctx = zmq.Context()

        output_pub = create_pub_socket(ctx, pub_addr)
        # output_pub.bind("tcp://*:0")
        # Get the port that was assigned
        # addr = socket.getsockopt(zmq.LAST_ENDPOINT).decode("utf-8")
        # port = addr.split(":")[-1]

        transcribe_sub = create_sub_socket(
            ctx, addition["transcribe_pub_addr"], ["transcribe"]
        )
        whisper_sub = create_sub_socket(
            ctx, addition["whisper_pub_addr"], ["transcribe"]
        )
        translation_sub = create_sub_socket(
            ctx, addition["translation_pub_addr"], ["translation"]
        )
        assistant_sub = create_sub_socket(
            ctx, addition["assistant_pub_addr"], ["assistant"]
        )

        is_exit = False

        def should_stop() -> bool:
            nonlocal is_exit
            if stop_flag.get() == 1:
                is_exit = True
            return is_exit

        def handle_sigint(signal_num, frame):
            nonlocal is_exit
            is_exit = True

        signal.signal(signal.SIGINT, handle_sigint)

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

        logger.info("rts2t worker process end.")
