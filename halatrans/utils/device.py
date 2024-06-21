import logging
from typing import Dict, Optional

import pyaudio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_audio_device_dict() -> Dict[int, str]:
    p = pyaudio.PyAudio()
    device_dict = {}
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        device_dict[i] = info["name"]
    return device_dict


def get_audio_device_index() -> Optional[int]:
    device_dict = get_audio_device_dict()
    selected_device: Optional[int] = None
    for idx, name in device_dict.items():
        if name.lower().strip() == "soundflower (2ch)":
            selected_device = idx
            break
    return selected_device
