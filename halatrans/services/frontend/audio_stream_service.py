import logging
# import signal
from dataclasses import dataclass
# from multiprocessing.managers import ValueProxy
from typing import Any, Dict, Generator, Optional

import sounddevice as sd

from halatrans.services.base_service import (PublishSubscribeService,
                                             ServiceConfig)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AudioStreamServiceParameters:
    samplerate: int = 16000
    blocksize: int = 8000
    channels: int = 1
    device: Optional[int] = None


class AudioStreamService(PublishSubscribeService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def on_worker_process_publisher(
        parameters: Dict[str, Any],
    ) -> Generator[bytes, Optional[str], None]:
        logger.info(f"Audio-Stream Service worker start, parameters: {parameters}")

        config = AudioStreamServiceParameters(**parameters)
        try:
            with sd.RawInputStream(
                device=config.device,  # stereo_mix_index, e.g. soundflow 2ch
                samplerate=config.samplerate,
                channels=config.channels,
                dtype="int16",
            ) as stream:
                while True:
                    data, overflowed = stream.read(config.blocksize)
                    if overflowed:
                        logger.warn("Warning: Buffer overflow!")

                    cmd = yield bytes(data)
                    if cmd == "STOP":
                        break
        except Exception as err:
            logger.error(err)

        logger.info("Audio-Stream Service worker end.")
