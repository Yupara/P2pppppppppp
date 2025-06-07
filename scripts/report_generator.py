import csv
from datetime import datetime
from models import Trade
from database import get_db

def generate_trade_report():
    db = next(get_db())
    trades = db.query(Trade).filter(Trade.status == "completed").all()
    
    filename = f"trade_report_{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Trade ID", "User ID", "Amount", "Currency", "Status", "Created At"])
        
        for trade in trades:
            writer.writerow([
                trade.id,
                trade.user_id,
                trade.amount,
                trade.currency,
                trade.status,
                trade.created_at
            ])
    
    return filename

# Пример использования
if __name__ == "__main__":
    report_file = generate_trade_report()
    print(f"Report generated: {report_file}")
