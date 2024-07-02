import logging
from dataclasses import asdict
from typing import Dict

from halatrans.services.base_service import BaseService, ServiceConfig
from halatrans.services.base_service_manager import BaseServiceManager
from halatrans.services.config import (CONST_AUDIO_DEVICE_REP_ADDR,
                                       CONST_AUDIO_DEVICE_SERVICE,
                                       CONST_AUDIO_STREAM_PUB_ADDR,
                                       CONST_AUDIO_STREAM_PUB_TOPIC,
                                       CONST_AUDIO_STREAM_SERVICE)
from halatrans.services.frontend.audio_device_service import (
    AudioDeviceService, AudioDeviceServiceParameters)
from halatrans.services.frontend.audio_stream_service import (
    AudioStreamService, AudioStreamServiceParameters)
from halatrans.services.process_task_manager import ServiceState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrontendServiceManager(BaseServiceManager):
    def __init__(self):
        super().__init__()

    def on_terminate(self):
        super().on_terminate()

    def on_prepare_start(self) -> ServiceState:
        service_state: Dict[str, BaseService] = {
            CONST_AUDIO_DEVICE_SERVICE: AudioDeviceService(
                ServiceConfig(
                    addr=CONST_AUDIO_DEVICE_REP_ADDR,
                    parameters=asdict(
                        AudioDeviceServiceParameters(),
                    ),
                )
            ),
        }

        return service_state

    def on_start_finished(self):
        pass

    def get_audio_device(self) -> AudioDeviceService:
        return self.get_service(CONST_AUDIO_DEVICE_SERVICE)

    def launch_audio_stream(self, parameters: AudioStreamServiceParameters):
        if CONST_AUDIO_STREAM_SERVICE in self.__service_state__:
            logger.error("Audio-Stream service is already running.")
            return

        service = AudioStreamService(
            ServiceConfig(
                addr=CONST_AUDIO_STREAM_PUB_ADDR,
                topic=CONST_AUDIO_STREAM_PUB_TOPIC,
                parameters=asdict(parameters),
            )
        )
        self.__service_state__[CONST_AUDIO_STREAM_SERVICE] = service
        self.__submit_task__(service)

    def stop_audio_stream(self):
        if CONST_AUDIO_STREAM_SERVICE not in self.__service_state__:
            logger.error("Audio-Stream service has been stopped.")
            return
        # TODO: stop one service
