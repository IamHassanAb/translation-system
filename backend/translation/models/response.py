from pydantic import BaseModel

class Request(BaseModel):
    source_lang: str
    target_lang: str
    text: str
    id: str