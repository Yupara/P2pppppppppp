from pydantic import BaseModel

class Ad(BaseModel):
    id: str
    type: str  # buy/sell
    amount: float
    price: float
    payment: str

class Trade(BaseModel):
    id: str
    ad: Ad
