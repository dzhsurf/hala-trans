import logging
import signal
from typing import Any, Dict, Optional, List
from multiprocessing.managers import ValueProxy

import zmq
import json
import os
from openai import OpenAI
import queue
import time
import threading

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import (
    create_pub_socket,
    create_sub_socket,
    poll_messages,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


prompt_sample_ask = """Translate below English texts into Chinese.
---
[0] The system message helps set the behavior of the assistant. 
[1] For example, you can modify the personality of the assistant or provide specific instructions about how it should behave throughout the conversation.
"""

prompt_sample_ans = """{
    "translations": [
        "系统消息帮助设置助手的行为",
        "例如，您可以修改助手的个性或提供有关其在整个对话过程中应如何表现的具体说明。"
    ]
}
"""


def openai_translate_text(client: OpenAI, text: str) -> str:
    prompt_user_ask = f"""Translate below English texts into Chinese.
---
{text}
"""
    # use openai to translate the text
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON.",
            },
            {
                "role": "user",
                "content": prompt_sample_ask,
            },
            {
                "role": "assistant",
                "content": prompt_sample_ans,
            },
            {
                "role": "user",
                "content": prompt_user_ask,
            },
        ],
    )
    content = response.choices[0].message.content
    result = json.loads(content)
    if "translation" in result:
        return result["translation"]
    if "translations" in result and isinstance(result["translations"], list):
        return "\n".join(result["translations"])
    return "[Unknow Format] " + content


def openai_translate_thread(input_queue: queue.Queue, output_queue: queue.Queue):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if len(api_key) == 0:
        logging.error("OpenAI: API_KEY is empty.")
        return
    openai_client = OpenAI(api_key=api_key)

    last_partial_translate = 0

    while True:
        chunk: Optional[bytes] = None
        try:
            chunk = input_queue.get(block=False)
        except queue.Empty:
            pass

        if chunk:
            if str(chunk, encoding='utf-8') == "STOP":
                output_queue.put("STOP")
                break
            
            logger.info(chunk)
            item = json.loads(chunk)
            msgid = item["msgid"]
            status = item["status"]
            text = item["text"]
            if status == "fulltext":
                # translate fulltext, final result
                translate_text = openai_translate_text(openai_client, text)
                logger.info(
                    f"---- translation ----\n{text}\n---- translation ----\n{translate_text}\n---- end ----\n"
                )
                # output
                translate_item = {
                    "msgid": msgid,
                    "status": "translate",
                    "text": text,
                    "translation": translate_text,
                }
                output_queue.put(json.dumps(translate_item))
            elif status == "partial":
                # translate partial text
                cur_partial_translate = time.time()
                # perform 1 seconds
                if cur_partial_translate - last_partial_translate > 2:
                    translate_text = openai_translate_text(openai_client, text)
                    logger.info(
                        f"---- translation ----\n{text}\n---- translation ----\n{translate_text}\n---- end ----\n"
                    )
                    # output
                    translate_item = {
                        "msgid": msgid,
                        "status": "translating",
                        "text": text,
                        "translation": translate_text,
                    }
                    output_queue.put(json.dumps(translate_item))
                    # update ts
                    last_partial_translate = time.time()
        else:
            time.sleep(0.1)


def translation_pub_thread(input_queue: queue.Queue, translation_pub_addr: str):
    ctx = zmq.Context()
    translation_pub = create_pub_socket(ctx, translation_pub_addr)

    while True:
        chunk: Optional[str] = None
        try:
            chunk = input_queue.get(block=False)
        except queue.Empty:
            pass

        if chunk:
            if chunk == "STOP":
                break
            translation_pub.send_multipart(
                [b"translation", bytes(chunk, encoding="utf-8")]
            )
        else:
            time.sleep(0.1)
    # cleanup
    translation_pub.close()


class TranslationService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(stop_flag: ValueProxy[int], pub_addr: Optional[str], addition: Dict[str, Any], *args):
        logger.info("start listening")

        condition_keys = [
            "translation_pub_addr",
            "whisper_pub_addr",
            "transcribe_pub_addr",
        ]
        for k in condition_keys:
            if k not in addition:
                raise ValueError(f"Key not exist: {k}")

        ctx = zmq.Context()
        whisper_sub = create_sub_socket(
            ctx, addition["whisper_pub_addr"], ["transcribe"]
        )
        transcribe_sub = create_sub_socket(
            ctx, addition["transcribe_pub_addr"], ["transcribe"]
        )

        # start openai thread
        logger.info("Start openai translate thread.")
        input_queue = queue.Queue(maxsize=10000)
        output_queue = queue.Queue(maxsize=10000)
        openai_thread = threading.Thread(
            target=openai_translate_thread,
            args=(
                input_queue,
                output_queue,
            ),
        )
        openai_thread.daemon = True
        openai_thread.start()

        # start pub thread
        pub_thread = threading.Thread(
            target=translation_pub_thread,
            args=(
                output_queue,
                addition["translation_pub_addr"],
            ),
        )
        pub_thread.daemon = True
        pub_thread.start()

        logger.info("Translation service start handle message...")

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

        def messages_handler(sock: zmq.Socket, chunks: List[bytes]):
            nonlocal input_queue

            for chunk in chunks:
                # item = json.loads(chunk)
                # msgid = item["msgid"]
                # text = item["text"]
                input_queue.put(chunk)

        poll_messages([whisper_sub, transcribe_sub], messages_handler, should_stop)

        # cleanup
        input_queue.put(bytes("STOP", encoding="utf-8"))
        openai_thread.join()
        pub_thread.join()

        whisper_sub.close()
        transcribe_sub.close()
