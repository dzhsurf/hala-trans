import logging
from typing import Any, Dict, Optional

import zmq

from halatrans.services.interface import BaseService, ServiceConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def receive_and_pub(sub: zmq.Socket, pub: zmq.Socket):
    temp_buf = []
    while True:
        try:
            topic, data = sub.recv_multipart(zmq.DONTWAIT)
            temp_buf.append(data)
            if len(temp_buf) > 20:
                break
        except zmq.Again:
            break

    for d in temp_buf:
        pub.send_multipart([b"rts2t", d])


class RTS2TService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(pub_addr: Optional[str], addition: Dict[str, Any], *args):
        # This is worker process
        logger.info("rts2t worker process start.")

        ctx = zmq.Context()

        output_pub = ctx.socket(zmq.PUB)
        output_pub.bind(pub_addr)
        # output_pub.bind("tcp://*:0")
        # Get the port that was assigned
        # addr = socket.getsockopt(zmq.LAST_ENDPOINT).decode("utf-8")
        # port = addr.split(":")[-1]

        transcribe_pub_addr = addition["transcribe_pub_addr"]

        transcribe_sub = ctx.socket(zmq.SUB)
        transcribe_sub.connect(transcribe_pub_addr)
        transcribe_sub.setsockopt(zmq.SUBSCRIBE, b"transcribe")

        whisper_pub_addr = addition["whisper_pub_addr"]

        whisper_sub = ctx.socket(zmq.SUB)
        whisper_sub.connect(whisper_pub_addr)
        whisper_sub.setsockopt(zmq.SUBSCRIBE, b"transcribe")

        poller = zmq.Poller()
        poller.register(transcribe_sub, zmq.POLLIN)
        poller.register(whisper_sub, zmq.POLLIN)

        while True:
            try:
                socks = dict(poller.poll())
            except KeyboardInterrupt:
                break

            if transcribe_sub in socks:
                receive_and_pub(transcribe_sub, output_pub)
            if whisper_sub in socks:
                receive_and_pub(whisper_sub, output_pub)

        logger.info("rts2t worker process end.")
