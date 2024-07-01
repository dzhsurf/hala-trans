from typing import Callable, List, Optional

import zmq


def nonblock_recv_multipart(sock: zmq.Socket) -> List[bytes]:
    BATCH_SIZE = 20
    chunks: List[bytes] = []
    while True:
        try:
            topic, chunk = sock.recv_multipart(zmq.DONTWAIT)
            chunks.append(chunk)
            if len(chunks) > BATCH_SIZE:
                break
        except zmq.Again:
            break
    return chunks


def create_pub_socket(ctx: zmq.Context, addr: str) -> zmq.Socket:
    pub = ctx.socket(zmq.PUB)
    pub.bind(addr)
    return pub


def create_sub_socket(ctx: zmq.Context, addr: str, topics: List[str]) -> zmq.Socket:
    sub = ctx.socket(zmq.SUB)
    sub.connect(addr)
    for topic in topics:
        sub.setsockopt(zmq.SUBSCRIBE, bytes(topic, encoding="utf-8"))
    return sub


def create_req_socket(ctx: zmq.Context, addr: str) -> zmq.Socket:
    req = ctx.socket(zmq.REQ)
    req.connect(addr)
    return req


def create_rep_socket(ctx: zmq.Context, addr: str) -> zmq.Socket:
    rep = ctx.socket(zmq.REP)
    rep.bind(addr)
    return rep


def handle_response_messages(
    sock: zmq.Socket,
    message_handler: Optional[Callable[[str, bytes], None]],
    should_stop: Optional[Callable[[], bool]] = None,
):
    while True:
        if should_stop and should_stop():
            break

        topic, chunk = sock.recv_multipart()
        if message_handler:
            response_data = message_handler(str(topic, encoding="utf-8"), chunk)
            sock.send_multipart([topic, response_data])
        else:
            sock.send_multipart([topic, ""])


def poll_messages(
    in_socks: List[zmq.Socket],
    message_handler: Optional[Callable[[zmq.Socket, List[bytes]], None]],
    should_stop: Optional[Callable[[], bool]] = None,
):
    poller = zmq.Poller()
    for sub_sock in in_socks:
        poller.register(sub_sock, zmq.POLLIN)

    while True:
        if should_stop and should_stop():
            break

        try:
            available_socks = dict(poller.poll(timeout=5000))
        except KeyboardInterrupt:
            break

        for sub_sock in in_socks:
            if sub_sock in available_socks:
                chunks = nonblock_recv_multipart(sub_sock)
                if message_handler:
                    message_handler(sub_sock, chunks)
