from pydantic import BaseModel


class ServiceRequest(BaseModel):
    cmd: str


class AudioStreamControlRequest(BaseModel):
    cmd: str
    deviceIndex: int
