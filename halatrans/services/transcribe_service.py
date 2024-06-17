import base64
import json
import logging

# from dataclasses import dataclass
from datetime import datetime
import signal
from typing import Any, Dict, List, Optional
from multiprocessing.managers import ValueProxy

import vosk
import zmq
from vosk import KaldiRecognizer

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import (
    create_pub_socket,
    create_sub_socket,
    poll_messages,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscribeService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(stop_flag: ValueProxy[int], pub_addr: Optional[str], addition: Dict[str, Any], *args):
        # json_config = args[0]
        # sample_rate = json_config["sample_rate"]
        sample_rate = 16000

        logger.info("Start init vosk...")
        model = vosk.Model(
            model_name="vosk-model-en-us-0.42-gigaspeech",
            lang="en-us",
        )
        recognizer = KaldiRecognizer(model, sample_rate)
        logger.info("Init vosk finish.")

        logger.info(f"Initial MQ, {addition}")

        condition_keys = ["transcribe_pub_addr", "audio_pub_addr"]
        for k in condition_keys:
            if k not in addition:
                raise ValueError(f"Key not exist: {k}")

        ctx = zmq.Context()

        transcribe_pub = create_pub_socket(ctx, addition["transcribe_pub_addr"])
        audio_sub = create_sub_socket(ctx, addition["audio_pub_addr"], ["audio"])

        logger.info("Transcribe service start handle message...")

        params: List[Optional[str]] = [None]  # msgid
        chunk_buff: List[bytes] = []

        is_exit = False

        def should_stop() -> bool:
            nonlocal is_exit
            if stop_flag.get() == 1:
                is_exit = True
            return is_exit
        
        def handle_sigint(signal_num, frame):
            nonlocal is_exit
            is_exit = True 
        signal.signal(signal.SIGINT, handle_sigint)

        def message_handler(sock: zmq.Socket, chunks: List[bytes]):
            nonlocal chunk_buff, params, transcribe_pub

            if params[0] is None:
                # TODO: gen id, and add ts to item
                ts = int(datetime.timestamp(datetime.now()))
                params[0] = f"msgid-{ts}"

            # batch handle chunks
            for chunk in chunks:
                if recognizer.AcceptWaveform(chunk):
                    recognizer.Reset()
                    # TODO: use faster-whisper instead
                    # res = json.loads(self.recognizer.Result())
                    # text = res["text"]

                    # output
                    item = {
                        "msgid": params[0],
                        "status": "fulltext",
                        "chunks": [
                            base64.b64encode(item).decode("utf-8")
                            for item in chunk_buff
                        ],
                    }

                    msg_body = bytes(json.dumps(item), encoding="utf-8")
                    transcribe_pub.send_multipart([b"prooftext", msg_body])

                    # reset
                    chunk_buff.clear()
                    params[0] = None
                else:
                    res = json.loads(recognizer.PartialResult())
                    text = res["partial"]
                    if len(text) > 2:
                        chunk_buff.append(chunk)

                        item = {
                            "msgid": params[0],
                            "status": "partial",
                            "text": text,
                        }
                        msg_body = bytes(json.dumps(item), encoding="utf-8")
                        transcribe_pub.send_multipart([b"transcribe", msg_body])

        poll_messages([audio_sub], message_handler, should_stop)

        # cleanup
        transcribe_pub.close()
        audio_sub.close()
