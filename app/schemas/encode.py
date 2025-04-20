from pydantic import BaseModel

class EncodeRequest(BaseModel):
    text: str

class EncodeResponse(BaseModel):
    embedding: list[float]
