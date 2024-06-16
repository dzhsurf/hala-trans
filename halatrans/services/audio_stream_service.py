import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import sounddevice as sd
import zmq

from halatrans.services.interface import BaseService, ServiceConfig

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
        # json_config = args[0]
        # json_config["port"] = 0
        # json_config["samplerate"] = 16000

        ctx = zmq.Context()

        config = DeviceConfig()
        logger.info("start listening, device: " + str(config))

        audio_pub_addr = addition["audio_pub_addr"]
        audio_pub = ctx.socket(zmq.PUB)
        audio_pub.bind(audio_pub_addr)

        try:
            with sd.RawInputStream(
                samplerate=config.samplerate, channels=config.channels, dtype="int16"
            ) as stream:
                while True:
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
