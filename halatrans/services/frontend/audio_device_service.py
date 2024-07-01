import json
import logging
import signal
from dataclasses import dataclass
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import zmq

from halatrans.services.base_service import BaseService, ServiceConfig
from halatrans.services.utils import (create_pub_socket, create_rep_socket,
                                      create_sub_socket,
                                      handle_response_messages, poll_messages)
from halatrans.utils.device import get_audio_device_dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AudioDeviceServiceParameters:
    pass


class AudioDeviceService(BaseService):
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
                return json.dumps(device_dict)

        except Exception:
            pass

        return None
