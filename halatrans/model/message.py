from pydantic import BaseModel


class MPQueueMsg(BaseModel):
    cmd: str
    body: bytes
