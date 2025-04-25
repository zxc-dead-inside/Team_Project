from pydantic import BaseModel


class MetricResponse(BaseModel):
    status: str = 'ok'
    receivded: int


class MetricRequest(BaseModel):
    timestamp: int
    user_email: str
    action: str
    object_type: str
    object_id: str