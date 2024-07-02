import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from halatrans.services.base_service import (RequestResponseService,
                                             ServiceConfig)
from halatrans.utils.device import get_audio_device_dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AudioDeviceServiceParameters:
    pass


class AudioDeviceService(RequestResponseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def on_worker_process_response(
        parameters: Dict[str, Any], topic: str, chunk: bytes
    ) -> Optional[bytes]:
        try:
            data = json.loads(chunk)
            # TODO: use pb instead
            cmd = data["cmd"]
            if cmd == "list-devices":
                device_dict = get_audio_device_dict()
                return bytes(json.dumps(device_dict), encoding="utf-8")
            else:
                return bytes(json.dumps({"err": "unknow command"}), encoding="utf-8")

        except Exception:
            pass

        return None
