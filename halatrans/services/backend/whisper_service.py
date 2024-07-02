import base64
import json
import logging
import os
from dataclasses import dataclass
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import numpy as np
import zmq
from faster_whisper import WhisperModel

from halatrans.services.base_service import CustomService, ServiceConfig
from halatrans.services.utils import (create_pub_socket, create_sub_socket,
                                      poll_messages)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INT16_MAX_ABS_VALUE = 32768.0
MIN_TEXT_LEN = 2


@dataclass
class WhisperServiceParameters:
    transcribe_pub_addr: str
    transcribe_pub_fulltext_topic: str
    whisper_pub_addr: str
    whisper_pub_topic: str


def process_faster_whisper_transcribe(
    faster_whipser: WhisperModel,
    msgid: str,
    frame_buffer: List[np.ndarray],
    whisper_pub: zmq.Socket,
    whisper_pub_topic: bytes,
):
    if len(frame_buffer) == 0:
        return

    combined_frames = np.concatenate(frame_buffer)

    segments, info = faster_whipser.transcribe(
        combined_frames,
        beam_size=5,
        language="en",
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    texts = []
    for segment in segments:
        text = segment.text.strip()
        # logger.info(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {text}")
        if len(text) > MIN_TEXT_LEN:
            texts.append(text)

    # update ui
    if len(texts) > 0:
        fulltext = " ".join(texts).strip()
        arr = fulltext.split(". ")
        fulltext = ".\n".join([s.strip() for s in arr])
        logger.info(f"\n--- {msgid} ---\n{fulltext}\n--- end ---\n")
        item = {
            "msgid": msgid,
            "status": "fulltext",
            "text": fulltext,
        }
        msg_body = bytes(json.dumps(item), encoding="utf-8")
        whisper_pub.send_multipart([whisper_pub_topic, msg_body])


class WhisperService(CustomService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def on_worker_process_custom(
        stop_flag: ValueProxy[int], parameters: Dict[str, Any]
    ):
        config = WhisperServiceParameters(**parameters)
        logger.info(f"WhisperService worker start. {config}")

        logger.info("Init faster whisper")
        os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
        model_size = "tiny.en"
        faster_whipser = WhisperModel(
            model_size,
            device="cpu",
            compute_type="float32",
            cpu_threads=0,
            num_workers=1,
        )

        logger.info("Initial MQ")
        ctx = zmq.Context()
        whisper_pub = create_pub_socket(ctx, config.whisper_pub_addr)
        transcribe_sub = create_sub_socket(
            ctx, config.transcribe_pub_addr, [config.transcribe_pub_fulltext_topic]
        )

        logger.info("Whisper service start handle message...")

        def should_stop() -> bool:
            if stop_flag.get() != 0:
                return True
            return False

        whisper_pub_topic = bytes(config.whisper_pub_topic, encoding="utf-8")

        def messages_handler(sock: zmq.Socket, chunks: List[bytes]):
            for chunk in chunks:
                item = json.loads(chunk)
                msgid = item["msgid"]
                b64_chunks = item["chunks"]
                frame_buffer: List[np.ndarray] = []
                for b64ecoded_text in b64_chunks:
                    chunk_bytes = base64.b64decode(b64ecoded_text)

                    frame = np.frombuffer(chunk_bytes, dtype=np.int16)
                    audio_array = frame.astype(np.float32) / INT16_MAX_ABS_VALUE
                    frame_buffer.append(audio_array)
                # use faster whisper to transcribe audio to text
                process_faster_whisper_transcribe(
                    faster_whipser=faster_whipser,
                    msgid=msgid,
                    frame_buffer=frame_buffer,
                    whisper_pub=whisper_pub,
                    whisper_pub_topic=whisper_pub_topic,
                )

        poll_messages([transcribe_sub], messages_handler, should_stop)

        # cleanup
        whisper_pub.close()
        transcribe_sub.close()
        ctx.term()

        logger.info("WhisperService worker end.")
