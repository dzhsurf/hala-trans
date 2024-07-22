import json
import logging
import os
from dataclasses import dataclass
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import zmq
from openai import OpenAI

from halatrans.services.base_service import CustomService, ServiceConfig
from halatrans.services.utils import (create_pub_socket, create_sub_socket,
                                      poll_messages)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AssistantServiceParameters:
    whisper_pub_addr: str
    whisper_pub_topic: str
    assistant_pub_addr: str
    assistant_pub_topic: str


def openai_chat_completions(client: OpenAI, text: str) -> str:
    # use openai to translate the text
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        # response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are ChatGPT, a large language model trained by OpenAI. Follow the user's instructions carefully. Respond using markdown.",
            },
            {
                "role": "user",
                "content": text,
            },
        ],
    )
    content = response.choices[0].message.content
    return content

# Do not use long sentence, response in short.
def process_openai_assistant(
    client: OpenAI,
    pub: zmq.Socket,
    topic: bytes,
    all_messages: List[str],
):
    user_prompt = """
Analyze the following conversation content, extract the main points using concise language, and provide advice for resolution.
---
"""

    all_texts = ""
    for msg in all_messages:
        all_texts += f"{msg}\n\n"

    all_texts = user_prompt + all_texts

    content = openai_chat_completions(client, all_texts)
    logger.info(content)

    item = {
        "msg_type": "assistant",
        "assistant": {
            "text": content,
        },
    }
    pub.send_multipart([topic, bytes(json.dumps(item), encoding="utf-8")])


class AssistantService(CustomService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def on_worker_process_custom(
        stop_flag: ValueProxy[int], parameters: Dict[str, Any]
    ):
        config = AssistantServiceParameters(**parameters)
        logger.info(f"AssistantService worker start. {config}")

        ctx = zmq.Context()
        whisper_sub = create_sub_socket(
            ctx, config.whisper_pub_addr, [config.whisper_pub_topic]
        )
        assistant_pub = create_pub_socket(ctx, config.assistant_pub_addr)

        api_key = os.getenv("OPENAI_API_KEY", "")
        client = OpenAI(api_key=api_key)

        def should_top() -> bool:
            if stop_flag.get() != 0:
                return True
            return False

        all_messages: List[str] = []

        assistant_pub_topic = bytes(config.assistant_pub_topic, encoding="utf-8")

        try:

            def message_handler(sock: zmq.Socket, chunks: List[bytes]):
                nonlocal all_messages, assistant_pub, assistant_pub_topic
                if len(chunks) == 0:
                    return

                for chunk in chunks:
                    item = json.loads(chunk)
                    # msgid = item["msgid"]
                    # status = item["status"]
                    text = item["text"]
                    all_messages.append(text)

                # need update
                SHIFT_WINDOW_SIZE = 5
                if len(all_messages) > SHIFT_WINDOW_SIZE:
                    process_openai_assistant(
                        client,
                        assistant_pub,
                        assistant_pub_topic,
                        all_messages[-SHIFT_WINDOW_SIZE:],
                    )
                else:
                    process_openai_assistant(
                        client, assistant_pub, assistant_pub_topic, all_messages
                    )

            poll_messages([whisper_sub], message_handler, should_top)
        except Exception as err:
            logger.error(err)
        finally:
            assistant_pub.close()
            whisper_sub.close()
            ctx.term()

        logger.info("AssistantService worker end.")
