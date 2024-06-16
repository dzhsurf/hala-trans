import json
import logging

# from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import base64
import numpy as np

import os
import zmq

from halatrans.services.interface import BaseService, ServiceConfig
from faster_whisper import WhisperModel

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

        whisper_pub_addr = addition["whisper_pub_addr"]
        whisper_pub = ctx.socket(zmq.PUB)
        whisper_pub.bind(whisper_pub_addr)

        transcribe_sub_addr = addition["transcribe_pub_addr"]
        transcribe_sub = ctx.socket(zmq.SUB)
        transcribe_sub.connect(transcribe_sub_addr)
        transcribe_sub.setsockopt(zmq.SUBSCRIBE, b"prooftext")

        poller = zmq.Poller()
        poller.register(transcribe_sub, zmq.POLLIN)

        logger.info("Whisper service start handle message...")

        msgid: Optional[str] = None
        # chunk_buff: List[bytes] = []
        while True:
            if msgid is None:
                ts = int(datetime.timestamp(datetime.now()))
                msgid = f"msgid-{ts}"

            # use poller to fetch audio data
            try:
                socks = dict(poller.poll())
            except KeyboardInterrupt:
                break

            # audio data available
            if transcribe_sub in socks:
                # fetch available chunks
                temp_chunks = []
                while True:
                    try:
                        topic, chunk = transcribe_sub.recv_multipart(zmq.DONTWAIT)
                        temp_chunks.append(chunk)
                        if len(temp_chunks) > 10:
                            break
                    except zmq.Again:
                        break

                # batch handle chunks
                for temp_chunk in temp_chunks:
                    item = json.loads(temp_chunk)
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
