import json
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import zmq
from openai import OpenAI

from halatrans.services.base_service import CustomService, ServiceConfig
from halatrans.services.utils import create_pub_socket, create_sub_socket, poll_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TranslationServiceParameters:
    transcribe_pub_addr: str
    transcribe_pub_partial_topic: str
    whisper_pub_addr: str
    whisper_pub_topic: str
    translation_pub_addr: str
    translation_pub_topic: str


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


def openai_translate_thread(
    stop_flag: ValueProxy[int],
    input_queue: queue.Queue,
    output_queue: queue.Queue,
):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if len(api_key) == 0:
        logging.error("OpenAI: API_KEY is empty.")
        return
    openai_client = OpenAI(api_key=api_key)

    last_partial_translate = 0

    while True:
        if stop_flag.get() != 0:
            break

        chunk: Optional[bytes] = None
        try:
            chunk = input_queue.get(block=False)
        except queue.Empty:
            pass

        if chunk:
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
                    # logger.info(
                    #     f"---- translation ----\n{text}\n---- translation ----\n{translate_text}\n---- end ----\n"
                    # )
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


def translation_pub_thread(
    stop_flag: ValueProxy[int],
    input_queue: queue.Queue,
    translation_pub_addr: str,
    translation_pub_topic: str,
):
    ctx = zmq.Context()
    translation_pub = create_pub_socket(ctx, translation_pub_addr)
    bytes_topic = bytes(translation_pub_topic, encoding="utf-8")

    while True:
        if stop_flag.get() != 0:
            break

        chunk: Optional[str] = None
        try:
            chunk = input_queue.get(block=False)
        except queue.Empty:
            pass

        if chunk:
            translation_pub.send_multipart(
                [bytes_topic, bytes(chunk, encoding="utf-8")]
            )
        else:
            time.sleep(0.1)
    # cleanup
    translation_pub.close()
    ctx.term()


class TranslationService(CustomService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def on_worker_process_custom(
        stop_flag: ValueProxy[int], parameters: Dict[str, Any]
    ):
        config = TranslationServiceParameters(**parameters)
        logger.info(f"TranslationService worker start. {config}")

        ctx = zmq.Context()
        whisper_sub = create_sub_socket(
            ctx, config.whisper_pub_addr, [config.whisper_pub_topic]
        )
        transcribe_sub = create_sub_socket(
            ctx, config.transcribe_pub_addr, [config.transcribe_pub_partial_topic]
        )

        # start openai thread
        logger.info("Start openai translate thread.")
        input_queue = queue.Queue(maxsize=10000)
        output_queue = queue.Queue(maxsize=10000)
        openai_thread = threading.Thread(
            target=openai_translate_thread,
            args=(
                stop_flag,
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
                stop_flag,
                output_queue,
                config.translation_pub_addr,
                config.translation_pub_topic,
            ),
        )
        pub_thread.daemon = True
        pub_thread.start()

        logger.info("Translation service start handle message...")

        def should_stop() -> bool:
            if stop_flag.get() != 0:
                return True
            return False

        try:

            def messages_handler(sock: zmq.Socket, chunks: List[bytes]):
                nonlocal input_queue
                for chunk in chunks:
                    # item = json.loads(chunk)
                    # msgid = item["msgid"]
                    # text = item["text"]
                    input_queue.put(chunk)

            poll_messages([whisper_sub, transcribe_sub], messages_handler, should_stop)
        except Exception as err:
            logger.error(err)
        finally:
            # cleanup
            openai_thread.join()
            pub_thread.join()

            whisper_sub.close()
            transcribe_sub.close()
            ctx.term()

        logger.info("TranslationService worker end.")
