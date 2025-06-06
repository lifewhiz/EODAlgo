from datetime import date
from datetime import time

MARKET_OPEN = time(13, 30)  # 9:30 AM ET (13:30 UTC)
MARKET_CLOSE = time(20, 0)  # 4:00 PM ET (20:00 UTC)

# Define the start and end dates for the strategy
START_DT = date(2025, 1, 1)
END_DT = date(2025, 5, 30)
