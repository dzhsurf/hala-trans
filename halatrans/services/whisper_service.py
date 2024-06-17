import base64
import json
import logging
import os

# from dataclasses import dataclass
from datetime import datetime
import signal
from typing import Any, Dict, List, Optional

import numpy as np
import zmq
from faster_whisper import WhisperModel

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import create_pub_socket, create_sub_socket, poll_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INT16_MAX_ABS_VALUE = 32768.0
MIN_TEXT_LEN = 2


def process_faster_whisper_transcribe(
    faster_whipser: WhisperModel,
    msgid: str,
    frame_buffer: List[np.ndarray],
    whisper_pub: zmq.Socket,
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
        whisper_pub.send_multipart([b"transcribe", msg_body])


class WhisperService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(pub_addr: Optional[str], addition: Dict[str, Any], *args):
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

        logger.info(f"Initial MQ, {addition}")

        condition_keys = ["transcribe_pub_addr", "whisper_pub_addr"]
        for k in condition_keys:
            if k not in addition:
                raise ValueError(f"Key not exist: {k}")

        ctx = zmq.Context()

        whisper_pub = create_pub_socket(ctx, addition["whisper_pub_addr"])
        transcribe_sub = create_sub_socket(
            ctx, addition["transcribe_pub_addr"], ["prooftext"]
        )

        logger.info("Whisper service start handle message...")

        is_exit = False

        def should_stop() -> bool:
            nonlocal is_exit
            return is_exit

        def handle_sigint(signal_num, frame):
            nonlocal is_exit
            is_exit = True

        signal.signal(signal.SIGINT, handle_sigint)

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
                )

        poll_messages([transcribe_sub], messages_handler, should_stop)

        # cleanup
        whisper_pub.close()
        transcribe_sub.close()
