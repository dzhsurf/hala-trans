import json
import logging

# from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import base64

import vosk
import zmq
from vosk import KaldiRecognizer

from halatrans.services.interface import BaseService, ServiceConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscribeService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(pub_addr: Optional[str], addition: Dict[str, Any], *args):
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

        transcribe_pub_addr = addition["transcribe_pub_addr"]
        transcribe_pub = ctx.socket(zmq.PUB)
        transcribe_pub.bind(transcribe_pub_addr)

        audio_pub_addr = addition["audio_pub_addr"]
        sub_audio = ctx.socket(zmq.SUB)
        sub_audio.connect(audio_pub_addr)
        sub_audio.setsockopt(zmq.SUBSCRIBE, b"audio")

        poller = zmq.Poller()
        poller.register(sub_audio, zmq.POLLIN)

        logger.info("Transcribe service start handle message...")

        msgid: Optional[str] = None
        chunk_buff: List[bytes] = []
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
            if sub_audio in socks:
                # fetch available chunks
                temp_chunks = []
                while True:
                    try:
                        topic, chunk = sub_audio.recv_multipart(zmq.DONTWAIT)
                        temp_chunks.append(chunk)
                        if len(temp_chunks) > 10:
                            break
                    except zmq.Again:
                        break

                # batch handle chunks
                for chunk in temp_chunks:
                    if recognizer.AcceptWaveform(chunk):
                        recognizer.Reset()
                        # TODO: use faster-whisper instead
                        # res = json.loads(self.recognizer.Result())
                        # text = res["text"]

                        # output
                        item = {
                            "msgid": msgid,
                            "status": "fulltext",
                            "chunks": [
                                base64.b64encode(item).decode("utf-8")
                                for item in chunk_buff
                            ],
                        }

                        msg_body = bytes(json.dumps(item), encoding="utf-8")
                        transcribe_pub.send_multipart([b"prooftext", msg_body])

                        # reset
                        chunk_buff = []
                        msgid = None
                    else:
                        res = json.loads(recognizer.PartialResult())
                        text = res["partial"]
                        if len(text) > 2:
                            chunk_buff.append(chunk)

                            item = {
                                "msgid": msgid,
                                "status": "partial",
                                "text": text,
                            }
                            msg_body = bytes(json.dumps(item), encoding="utf-8")
                            transcribe_pub.send_multipart([b"transcribe", msg_body])
