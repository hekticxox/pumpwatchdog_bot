# Top 25 Indicators for Forward Price Movement Prediction

These indicators are popular for algorithmic trading, quant research, and discretionary analysis. Many are used as features in machine learning models as well.

---

## Trend & Momentum

1. **Moving Averages** (SMA, EMA, WMA)
   - Smooth price data to show trend direction.
2. **MACD** (Moving Average Convergence Divergence)
   - Shows momentum and trend changes.
3. **RSI** (Relative Strength Index)
   - Measures speed and change of price movements (momentum/overbought/oversold).
4. **Stochastic Oscillator**
   - Compares closing price to a price range.
5. **ADX/DMI** (Average Directional Index / Directional Movement)
   - Quantifies trend strength.

## Volatility & Bands

6. **Bollinger Bands**
   - Volatility bands placed above and below a moving average.
7. **ATR** (Average True Range)
   - Measures market volatility.
8. **Donchian Channels**
   - Highest high and lowest low over a set period.
9. **Keltner Channels**
   - Volatility-based envelopes set above/below EMA.

## Volume & Order Flow

10. **OBV** (On-Balance Volume)
    - Cumulative volume flow.
11. **Volume Weighted Average Price (VWAP)**
    - Average price weighted by volume.
12. **Chaikin Money Flow (CMF)**
    - Combines price and volume to show buying/selling pressure.
13. **Accumulation/Distribution Line**
    - Measures supply/demand by looking at price and volume.

## Price Action & Reversal

14. **Pivot Points**
    - Key price levels based on previous highs/lows/closes.
15. **Fibonacci Retracement/Extension Levels**
    - Predicts support/resistance based on Fibonacci ratios.
16. **Candlestick Patterns** (e.g., Doji, Engulfing, Hammer)
    - Visual reversal or continuation signals.

## Oscillators & Others

17. **CCI** (Commodity Channel Index)
    - Identifies cyclical trends.
18. **Williams %R**
    - Momentum indicator similar to Stochastic.
19. **ROC** (Rate of Change)
    - Measures speed of price movement.
20. **TRIX**
    - Triple-smoothed exponential moving average.

## Machine Learning Features & Hybrid

21. **Price Rate of Change/Returns**
    - Simple percent change or log returns.
22. **Momentum (n-period price difference)**
    - Measures the difference between current and past price.
23. **Z-Score of Price/Volume**
    - Normalized price or volume for anomaly detection.
24. **Fractal Dimension Index**
    - Measures market "roughness" or trendiness.
25. **Custom Features/Alphas**
    - e.g., RSI/MACD crossovers, moving average crossovers, volatility breakout signals, etc.

---

## Notes

- **No single indicator predicts the future**; combinations and context matter.
- For best results, use a mix of trend, momentum, volume, and volatility indicators.
- Feature engineering (derivatives, lags, crossovers, rolling windows) improves predictive power, especially in ML models.
- Always validate on out-of-sample data and beware of overfitting.

---

## References

- [Technical Indicators on Investopedia](https://www.investopedia.com/terms/t/technicalindicator.asp)
- [TA-Lib Indicator List](https://mrjbq7.github.io/ta-lib/funcs.html)
- [Kaggle/Quantopian Forums](https://www.quantopian.com/posts/the-ultimate-list-of-alpha-factors)