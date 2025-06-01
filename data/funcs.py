INDEX_DT = {
    "SPX": {
        "option_symbol": "SPXW",
        "stock_symbol": "^SPX",
    }
}


def get_option_symbol(symbol: str) -> str:
    return INDEX_DT[symbol]["option_symbol"] if symbol in INDEX_DT else symbol


def get_stock_symbol(symbol: str) -> str:
    return INDEX_DT[symbol]["stock_symbol"] if symbol in INDEX_DT else symbol
