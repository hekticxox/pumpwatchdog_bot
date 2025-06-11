def get_order_book_metrics(exchange, symbol, order_book_depth=10):
    """
    Analyze order book for liquidity and spread metrics.

    Returns a dictionary:
        {
            "buy_liquidity": sum of top N bids,
            "sell_liquidity": sum of top N asks,
            "spread": best ask - best bid,
            "imbalance": buy_liquidity / (sell_liquidity + 1e-9)
        }
    """
    try:
        ob = exchange.fetch_order_book(symbol)
        buy_liquidity = sum([x[1] for x in ob['bids'][:order_book_depth]])
        sell_liquidity = sum([x[1] for x in ob['asks'][:order_book_depth]])
        spread = ob['asks'][0][0] - ob['bids'][0][0]
        imbalance = buy_liquidity / (sell_liquidity + 1e-9)
        return {
            "buy_liquidity": buy_liquidity,
            "sell_liquidity": sell_liquidity,
            "spread": spread,
            "imbalance": imbalance
        }
    except Exception as e:
        # In case of any error (API, symbol not found, etc.), return zeros
        return {
            "buy_liquidity": 0,
            "sell_liquidity": 0,
            "spread": 9999,
            "imbalance": 0
        }
