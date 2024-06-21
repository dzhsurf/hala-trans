import logging
import signal
from dataclasses import dataclass
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, Optional

import sounddevice as sd
import zmq

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import create_pub_socket
from halatrans.utils.device import get_audio_device_index

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
    def process_worker(
        stop_flag: ValueProxy[int],
        pub_addr: Optional[str],
        addition: Dict[str, Any],
        *args,
    ):
        ctx = zmq.Context()

        config = DeviceConfig()
        logger.info("start listening, device: " + str(config))

        audio_pub = create_pub_socket(ctx, addition["audio_pub_addr"])

        is_exit = False

        def handle_sigint(signal_num, frame):
            nonlocal is_exit
            is_exit = True

        signal.signal(signal.SIGINT, handle_sigint)

        selected_device = get_audio_device_index()
        logger.info(f"Selected Device: {selected_device}")

        try:
            with sd.RawInputStream(
                device=selected_device,  # stereo_mix_index, e.g. soundflow 2ch
                samplerate=config.samplerate,
                channels=config.channels,
                dtype="int16",
            ) as stream:
                while not is_exit and stop_flag.get() == 0:
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
