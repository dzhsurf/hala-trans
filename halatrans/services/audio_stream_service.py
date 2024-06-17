import logging
from dataclasses import dataclass
import signal
from typing import Any, Dict, Optional

import sounddevice as sd
import zmq

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import create_pub_socket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeviceConfig:
    samplerate: int = 16000
    blocksize: int = 8000
    channels: int = 1
    device: Optional[int] = None


class AudioStreamService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(pub_addr: Optional[str], addition: Dict[str, Any], *args):
        ctx = zmq.Context()

        config = DeviceConfig()
        logger.info("start listening, device: " + str(config))

        audio_pub = create_pub_socket(ctx, addition["audio_pub_addr"])

        is_exit = False

        def handle_sigint(signal_num, frame):
            nonlocal is_exit
            is_exit = True

        signal.signal(signal.SIGINT, handle_sigint)

        try:
            with sd.RawInputStream(
                samplerate=config.samplerate, channels=config.channels, dtype="int16"
            ) as stream:
                while not is_exit:
                    data, overflowed = stream.read(config.blocksize)
                    if overflowed:
                        logger.warn("Warning: Buffer overflow!")

                    # publish audio stream
                    audio_pub.send_multipart([b"audio", bytes(data)])
        except Exception as e:
            logger.error(e)
        finally:
            audio_pub.close()
            logger.info("Exit listening.")
