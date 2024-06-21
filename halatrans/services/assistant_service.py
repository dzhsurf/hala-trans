import logging
import os
import signal
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import zmq
import json
from openai import OpenAI

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import create_pub_socket, create_sub_socket, poll_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def openai_chat_completions(client: OpenAI, text: str) -> str:
    # use openai to translate the text
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
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

# extract the technical/design question from the conversation
# then answer the question
# 下面内容是面试过程的招聘者的语音对话内容,忽略里面的闲聊和与技术无关的信息问题,提取面试者的问题内容。使用json格式返回。
# 例如 
# { questions: ["Why are you interested in the position in Lyft?", "Talk about your work experiences."] }

# Do not use long sentence, response in short.
def process_openai_assistant(client: OpenAI, pub: zmq.Socket, all_messages: List[str]):
    user_prompt = """Below is the interviewer's speech transcription during an interview process. 
Ignore small talk and non-technical information questions, and extract the questions asked by the interviewer.
And format the output as JSON. For example here is the output: { questions: ["Why are you interested in the position in Lyft?", "Talk about your work experiences."] } 
If there're no questions in the context, response: { questions: [] }
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
    pub.send_multipart([b"assistant", bytes(json.dumps(item), encoding="utf-8")])


class AssistantService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(
        stop_flag: ValueProxy[int],
        pub_addr: Optional[str],
        addition: Dict[str, Any],
        *args,
    ):
        logger.info("Init assistant service")

        ctx = zmq.Context()
        whisper_sub = create_sub_socket(
            ctx, addition["whisper_pub_addr"], ["transcribe"]
        )

        assistant_pub = create_pub_socket(ctx, addition["assistant_pub_addr"])

        api_key = os.getenv("OPENAI_API_KEY", "")
        client = OpenAI(api_key=api_key)

        def should_top() -> bool:
            nonlocal stop_flag
            if stop_flag.get() == 1:
                return True
            return False

        def handle_sigint(signal_num, frame):
            nonlocal stop_flag
            stop_flag.set(1)

        signal.signal(signal.SIGINT, handle_sigint)

        all_messages: List[str] = []

        def message_handler(sock: zmq.Socket, chunks: List[bytes]):
            nonlocal all_messages, assistant_pub
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
                process_openai_assistant(client, assistant_pub, all_messages[-SHIFT_WINDOW_SIZE:])
            else:
                process_openai_assistant(client, assistant_pub, all_messages)

        poll_messages([whisper_sub], message_handler, should_top)
