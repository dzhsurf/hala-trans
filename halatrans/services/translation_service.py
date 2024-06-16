import logging
from typing import Any, Dict, Optional

import zmq

from halatrans.services.interface import BaseService, ServiceConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranslationService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(pub_addr: Optional[str], addition: Dict[str, Any], *args):

        ctx = zmq.Context()

        logger.info("start listening")

        audio_pub_addr = addition["audio_pub_addr"]
        audio_pub = ctx.socket(zmq.PUB)
        audio_pub.bind(audio_pub_addr)
