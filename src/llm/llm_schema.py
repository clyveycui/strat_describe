from pydantic import BaseModel

class Move(BaseModel):
    reason: str
    move: str

class StrategyDescription(BaseModel):
    description: str