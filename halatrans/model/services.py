from pydantic import BaseModel


class ServiceRequest(BaseModel):
    service_name: str
