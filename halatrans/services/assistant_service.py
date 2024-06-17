import logging
import signal
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import zmq

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import create_pub_socket, create_sub_socket, poll_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AssistantService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(
        stop_flag: ValueProxy[int],
        pub_addr: Optional[str],
        addition: Dict[str, Any],
        *args,
    ):
        logger.info("Init assistant service")

        ctx = zmq.Context()
        whisper_sub = create_sub_socket(
            ctx, addition["whisper_pub_addr"], ["transcribe"]
        )

        assistant_pub = create_pub_socket(ctx, addition["assistant_pub_addr"])

        def should_top() -> bool:
            nonlocal stop_flag
            if stop_flag.get() == 1:
                return True
            return False

        def handle_sigint(signal_num, frame):
            nonlocal stop_flag
            stop_flag.set(1)

        signal.signal(signal.SIGINT, handle_sigint)

        def message_handler(sock: zmq.Socket, chunks: List[bytes]):
            pass

        poll_messages([whisper_sub], message_handler, should_top)
