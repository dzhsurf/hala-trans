import logging
from typing import Any, Dict, Optional, List

import zmq

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import (
    create_pub_socket,
    create_sub_socket,
    poll_messages,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranslationService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(pub_addr: Optional[str], addition: Dict[str, Any], *args):
        ctx = zmq.Context()

        logger.info("start listening")

        condition_keys = ["translation_pub_addr", "whisper_pub_addr"]
        for k in condition_keys:
            if k not in addition:
                raise ValueError(f"Key not exist: {k}")

        ctx = zmq.Context()

        translation_pub = create_pub_socket(ctx, addition["translation_pub_addr"])
        whisper_sub = create_sub_socket(
            ctx, addition["whisper_pub_addr"], ["transcribe"]
        )

        logger.info("Translation service start handle message...")

        def messages_handler(sock: zmq.Socket, chunks: List[bytes]):
            nonlocal translation_pub

            # translation_pub.send_multipart([b'', ''])

        poll_messages([whisper_sub], messages_handler)
