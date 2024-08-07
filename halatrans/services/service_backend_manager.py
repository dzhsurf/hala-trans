import logging
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, Tuple  # noqa: F401

from halatrans.services.backend.assistant_service import (
    AssistantService, AssistantServiceParameters)
from halatrans.services.backend.rts2t_service import (RTS2TService,
                                                      RTS2TServiceParameters)
from halatrans.services.backend.storage_service import (
    StorageService, StorageServiceParameters)
from halatrans.services.backend.transcribe_service import (
    TranscribeService, TranscribeServiceParameters)
from halatrans.services.backend.translation_service import (
    TranslationService, TranslationServiceParameters)
from halatrans.services.backend.whisper_service import (
    WhisperService, WhisperServiceParameters)
from halatrans.services.base_service import BaseService, ServiceConfig
from halatrans.services.base_service_manager import BaseServiceManager
from halatrans.services.config import (CONST_ASSISTANT_PUB_ADDR,
                                       CONST_ASSISTANT_PUB_TOPIC,
                                       CONST_AUDIO_STREAM_PUB_ADDR,
                                       CONST_AUDIO_STREAM_PUB_TOPIC,
                                       CONST_RTS2T_PUB_ADDR,
                                       CONST_RTS2T_PUB_TOPIC,
                                       CONST_TRANSCRIBE_PUB_ADDR,
                                       CONST_TRANSCRIBE_PUB_FULLTEXT_TOPIC,
                                       CONST_TRANSCRIBE_PUB_PARTIAL_TOPIC,
                                       CONST_TRANSLATION_PUB_ADDR,
                                       CONST_TRANSLATION_PUB_TOPIC,
                                       CONST_WHISPER_PUB_ADDR,
                                       CONST_WHISPER_PUB_TOPIC)
from halatrans.services.process_task_manager import ServiceState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackendServiceManager(BaseServiceManager):
    def __init__(self):
        super().__init__()

    def on_terminate(self):
        # TODO: must control sub services shutdown order.
        return super().on_terminate()

    def on_prepare_start(self) -> ServiceState:
        service_state: Dict[str, BaseService] = {
            "rts2t-main": RTS2TService(
                ServiceConfig(
                    parameters=asdict(
                        RTS2TServiceParameters(
                            output_pub_addr=CONST_RTS2T_PUB_ADDR,
                            output_pub_topic=CONST_RTS2T_PUB_TOPIC,
                            transcribe_pub_addr=CONST_TRANSCRIBE_PUB_ADDR,
                            transcribe_pub_partial_topic=CONST_TRANSCRIBE_PUB_PARTIAL_TOPIC,
                            whisper_pub_addr=CONST_WHISPER_PUB_ADDR,
                            whisper_pub_topic=CONST_WHISPER_PUB_TOPIC,
                            translation_pub_addr=CONST_TRANSLATION_PUB_ADDR,
                            translation_pub_topic=CONST_TRANSLATION_PUB_TOPIC,
                            assistant_pub_addr=CONST_ASSISTANT_PUB_ADDR,
                            assistant_pub_topic=CONST_ASSISTANT_PUB_TOPIC,
                        )
                    ),
                )
            ),
            "rts2t-transcribe": TranscribeService(
                ServiceConfig(
                    parameters=asdict(
                        TranscribeServiceParameters(
                            audio_pub_addr=CONST_AUDIO_STREAM_PUB_ADDR,
                            audio_pub_topic=CONST_AUDIO_STREAM_PUB_TOPIC,
                            transcribe_pub_addr=CONST_TRANSCRIBE_PUB_ADDR,
                            transcribe_pub_partial_topic=CONST_TRANSCRIBE_PUB_PARTIAL_TOPIC,
                            transcribe_pub_fulltext_topic=CONST_TRANSCRIBE_PUB_FULLTEXT_TOPIC,
                        )
                    ),
                )
            ),
            "rts2t-whisper": WhisperService(
                ServiceConfig(
                    parameters=asdict(
                        WhisperServiceParameters(
                            transcribe_pub_addr=CONST_TRANSCRIBE_PUB_ADDR,
                            transcribe_pub_fulltext_topic=CONST_TRANSCRIBE_PUB_FULLTEXT_TOPIC,
                            whisper_pub_addr=CONST_WHISPER_PUB_ADDR,
                            whisper_pub_topic=CONST_WHISPER_PUB_TOPIC,
                        )
                    ),
                )
            ),
            "rts2t-translation": TranslationService(
                ServiceConfig(
                    parameters=asdict(
                        TranslationServiceParameters(
                            transcribe_pub_addr=CONST_TRANSCRIBE_PUB_ADDR,
                            transcribe_pub_partial_topic=CONST_TRANSCRIBE_PUB_PARTIAL_TOPIC,
                            whisper_pub_addr=CONST_WHISPER_PUB_ADDR,
                            whisper_pub_topic=CONST_WHISPER_PUB_TOPIC,
                            translation_pub_addr=CONST_TRANSLATION_PUB_ADDR,
                            translation_pub_topic=CONST_TRANSLATION_PUB_TOPIC,
                        )
                    ),
                )
            ),
            "rts2t-assistant": AssistantService(
                ServiceConfig(
                    parameters=asdict(
                        AssistantServiceParameters(
                            whisper_pub_addr=CONST_WHISPER_PUB_ADDR,
                            whisper_pub_topic=CONST_WHISPER_PUB_TOPIC,
                            assistant_pub_addr=CONST_ASSISTANT_PUB_ADDR,
                            assistant_pub_topic=CONST_ASSISTANT_PUB_TOPIC,
                        )
                    ),
                )
            ),
            "rts2t-storage": StorageService(
                ServiceConfig(
                    parameters=asdict(
                        StorageServiceParameters(
                            transcribe_pub_addr=CONST_TRANSCRIBE_PUB_ADDR,
                            transcribe_pub_fulltext_topic=CONST_TRANSCRIBE_PUB_FULLTEXT_TOPIC,
                            translation_pub_addr=CONST_TRANSLATION_PUB_ADDR,
                            translation_pub_topic=CONST_TRANSLATION_PUB_TOPIC,
                        )
                    ),
                )
            ),
        }

        return service_state

    def run_command(self, cmd: str) -> str:
        logger.info(f"Run command {cmd}")

        if cmd == "start":
            return self.start()
        elif cmd == "stop":
            return self.stop()

        return "Unknow command"
