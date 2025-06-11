from pydantic import BaseModel

class Ad(BaseModel):
    id: str
    type: str  # buy or sell
    amount: float
    price: float
    payment: str

class Trade(BaseModel):
    id: str
    ad: Ad
