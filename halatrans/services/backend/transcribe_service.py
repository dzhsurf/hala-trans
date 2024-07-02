import base64
import json
import logging
from dataclasses import dataclass

# from dataclasses import dataclass
from datetime import datetime
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import vosk
import zmq
from vosk import KaldiRecognizer

from halatrans.services.base_service import CustomService, ServiceConfig
from halatrans.services.utils import create_pub_socket, create_sub_socket, poll_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TranscribeServiceParameters:
    audio_pub_addr: str
    audio_pub_topic: str
    transcribe_pub_addr: str
    transcribe_pub_partial_topic: str
    transcribe_pub_fulltext_topic: str


class TranscribeService(CustomService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def on_worker_process_custom(
        stop_flag: ValueProxy[int], parameters: Dict[str, Any]
    ):
        config = TranscribeServiceParameters(**parameters)
        logger.info(f"TranscribeService worker start. {config}")

        sample_rate = 16000

        logger.info("Start init vosk...")
        model = vosk.Model(
            model_name="vosk-model-en-us-0.42-gigaspeech",
            lang="en-us",
        )
        recognizer = KaldiRecognizer(model, sample_rate)
        logger.info("Init vosk finish.")

        logger.info("Initial MQ")

        ctx = zmq.Context()

        transcribe_pub = create_pub_socket(ctx, config.transcribe_pub_addr)
        audio_sub = create_sub_socket(
            ctx, config.audio_pub_addr, [config.audio_pub_topic]
        )

        logger.info("Transcribe service start handle message...")

        params: List[Optional[str]] = [None]  # msgid
        chunk_buff: List[bytes] = []

        def should_stop() -> bool:
            if stop_flag.get() != 0:
                return True
            return False

        partial_topic = bytes(config.transcribe_pub_partial_topic, encoding="utf-8")
        fulltext_topic = bytes(config.transcribe_pub_fulltext_topic, encoding="utf-8")

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
                    transcribe_pub.send_multipart([fulltext_topic, msg_body])

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
                        transcribe_pub.send_multipart([partial_topic, msg_body])

        poll_messages([audio_sub], message_handler, should_stop)

        # cleanup
        transcribe_pub.close()
        audio_sub.close()
        ctx.term()

        logger.info("TranscribeService worker end.")
