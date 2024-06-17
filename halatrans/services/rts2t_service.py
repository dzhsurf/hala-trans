import logging
from typing import Any, Dict, Optional, List

import zmq

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import create_pub_socket, create_sub_socket, poll_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RTS2TService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(pub_addr: Optional[str], addition: Dict[str, Any], *args):
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

        poller = zmq.Poller()
        poller.register(transcribe_sub, zmq.POLLIN)
        poller.register(whisper_sub, zmq.POLLIN)

        def message_handler(sock: zmq.Socket, chunks: List[bytes]):
            nonlocal output_pub
            for chunk in chunks:
                output_pub.send_multipart([b"rts2t", chunk])

        poll_messages([transcribe_sub, whisper_sub], message_handler)

        logger.info("rts2t worker process end.")
