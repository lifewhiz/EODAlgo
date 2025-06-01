import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Field
from pandera.typing import Series, Date


class CandleModel(pa.DataFrameModel):
    timestamp: Series[pd.DatetimeTZDtype] = Field(
        dtype_kwargs={"unit": "ns", "tz": "UTC"}
    )
    open: Series[float]
    high: Series[float]
    low: Series[float]
    close: Series[float]
    volume: Series[float] = Field(nullable=True)
    vwap: Series[float] = Field(nullable=True)
    date: Series[Date]

    class Config:
        strict = True
        coerce = True
