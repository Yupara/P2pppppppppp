from sqlalchemy import Enum as PgEnum
import enum

class TradeStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    completed = "completed"
    canceled = "canceled"

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    ad_id = Column(Integer, ForeignKey("ads.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    status = Column(PgEnum(TradeStatus), default=TradeStatus.pending)

    # ... другие связи
