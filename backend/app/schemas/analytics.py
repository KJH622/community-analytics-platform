from pydantic import BaseModel


class KeywordTrendPoint(BaseModel):
    keyword: str
    mentions: int


class TopicBreakdownPoint(BaseModel):
    topic: str
    documents: int
