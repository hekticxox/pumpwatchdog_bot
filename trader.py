import logging
from typing import Optional
import ccxt

class Trader:
    """
    Handles trading and balance checking for KuCoin using ccxt.
    Designed with test mode for safe development.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        password: str,
        test_mode: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Trader object.

        Args:
            api_key (str): KuCoin API key.
            api_secret (str): KuCoin API secret.
            password (str): KuCoin API passphrase.
            test_mode (bool, optional): If True, disables trading. Defaults to True.
            logger (Optional[logging.Logger]): Logger instance. Defaults to None.
        """
        self.test_mode = test_mode
        self.logger = logger or logging.getLogger("Trader")
        self.exchange = ccxt.kucoin({
            'apiKey': api_key,
            'secret': api_secret,
            'password': password,
            'enableRateLimit': True,
        })

    def get_balance(self, asset: str = "USDT") -> float:
        """
        Fetch free balance for a given asset.

        Args:
            asset (str, optional): Asset symbol. Defaults to "USDT".

        Returns:
            float: Free balance amount, or 0 if error.
        """
        try:
            balance = self.exchange.fetch_balance()
            return balance.get('free', {}).get(asset, 0)
        except Exception as e:
            self.logger.error(f"[BALANCE ERROR] {e}")
            return 0.0

    def place_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        order_type: str = "limit"
    ) -> Optional[dict]:
        """
        Place an order on KuCoin.

        Args:
            symbol (str): Trading pair symbol (e.g., "BTC/USDT").
            side (str): "buy" or "sell".
            amount (float): Amount to buy/sell.
            price (Optional[float], optional): Price for limit order. Defaults to None.
            order_type (str, optional): "limit" or "market". Defaults to "limit".

        Returns:
            Optional[dict]: Order response dict, or None if error or test_mode.
        """
        if self.test_mode:
            self.logger.info(f"[TEST MODE] Would place {order_type} {side} order: {amount} {symbol} at {price}")
            return None

        try:
            if order_type == "market":
                order = self.exchange.create_market_order(symbol, side, amount)
            else:
                if price is None:
                    raise ValueError("Limit orders require a price.")
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            self.logger.info(f"[ORDER] Placed {order_type} {side} order: {order}")
            return order
        except Exception as e:
            self.logger.error(f"[ORDER ERROR] {e}")
            return None

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("KUCOIN_API_KEY", "")
    api_secret = os.getenv("KUCOIN_SECRET", "")
    api_password = os.getenv("KUCOIN_PASSWORD", "")

    logging.basicConfig(level=logging.INFO)
    trader = Trader(api_key, api_secret, api_password, test_mode=True)

    # Example usage
    print("USDT Balance:", trader.get_balance())
    trader.place_order("BTC/USDT", "buy", 0.001, price=30000)
