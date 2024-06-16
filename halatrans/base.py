from dataclasses import asdict, dataclass
from enum import Enum
from typing import List


class PROCESS_TEXT_STATUS(Enum):
    TEXTING = "TEXTING"
    FULLTEXT = "FULLTEXT"
    OPENAI_CONVERT = "OPENAI_CONVERT"
    ASSISTANT = "ASSISTANT"


@dataclass
class BaseDataClass:
    def __iter__(self):
        for attribute, value in asdict(self).items():
            if isinstance(value, Enum):
                yield (attribute, str(value))
            else:
                yield (attribute, value)


@dataclass
class MsgBubble(BaseDataClass):
    msgid: str
    status: PROCESS_TEXT_STATUS
    texts: List[str]
    translations: List[str] | None
