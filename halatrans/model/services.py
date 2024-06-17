from pydantic import BaseModel


class ServiceRequest(BaseModel):
    cmd: str
