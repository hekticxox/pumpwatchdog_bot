import ccxt

def get_orderbook_imbalance(symbol, exchange_name='kucoin', depth=10):
    """
    Fetches the order book and computes the bid/ask imbalance for the top N levels.
    Returns:
        - imbalance (float): between -1 and 1
        - top_bids (float): sum of top N bid sizes * prices
        - top_asks (float): sum of top N ask sizes * prices
    """
    exchange = getattr(ccxt, exchange_name)()
    orderbook = exchange.fetch_order_book(symbol)
    top_bids = sum([price * amount for price, amount in orderbook['bids'][:depth]])
    top_asks = sum([price * amount for price, amount in orderbook['asks'][:depth]])
    if top_bids + top_asks == 0:
        return 0, top_bids, top_asks  # Avoid division by zero
    imbalance = (top_bids - top_asks) / (top_bids + top_asks)
    return imbalance, top_bids, top_asks
