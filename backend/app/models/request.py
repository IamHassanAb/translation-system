from pydantic import BaseModel

class TranslationRequest(BaseModel):
    source_language: str
    target_language: str
    text: str
    id: str