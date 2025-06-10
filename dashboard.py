from flask import Flask, render_template_string, jsonify
import threading
import json
import os

app = Flask(__name__)

SIGNALS_FILE = "signals.json"

LEGEND_HTML = """
<div style="background: #fafafa; border: 1px solid #ccc; padding: 1em; margin-bottom: 1.5em; border-radius: 6px;">
  <h3>PumpWatchdog Signal Score Legend</h3>
  <b>Maximum Possible Score: 14</b><br>
  Each point in the score reflects a bullish signal triggered by a technical indicator or pattern.<br>
  <b>A higher score means more bullish signals are aligning for that trading pair.</b>
  <ul>
    <li><b>RSI_DIVERGENCE</b>: RSI bullish divergence detected</li>
    <li><b>MACD_DIVERGENCE</b>: MACD bullish divergence detected</li>
    <li><b>RVOL</b>: Relative volume &gt; 2.0 (recent volume surge)</li>
    <li><b>MTF_BULL</b>: Higher timeframe (1h) bullish candle</li>
    <li><b>HAMMER</b>: Hammer candlestick pattern detected</li>
    <li><b>ENGULFING</b>: Bullish engulfing pattern detected</li>
    <li><b>RETEST</b>: Breakout with successful retest</li>
    <li><b>PB</b>: Price breakout above recent high</li>
    <li><b>BULL</b>: Latest candle is bullish (close &gt; open)</li>
    <li><b>TRIANGLE</b>: Triangle pattern detected</li>
    <li><b>PREPUMP</b>: Pre-pump conditions (volume/volatility surge without price move)</li>
    <li><b>MACD</b>: MACD bullish (MACD diff &gt; 0)</li>
    <li><b>STOCH</b>: Stochastic Oscillator &gt; 80 (overbought momentum)</li>
    <li><b>VWAP</b>: Price above VWAP</li>
  </ul>
  <i>A score of 14 means all bullish signals are present at once — this is extremely rare. In practice, scores of 5–8 often indicate strong setups.</i>
</div>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PumpWatchdog Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2em; background: #f5f6fa;}
        table { border-collapse: collapse; width: 100%; background: #fff; }
        th, td { border: 1px solid #ddd; padding: 0.5em; text-align: center; }
        th { background: #eee; }
        tr:nth-child(even) { background: #f9f9f9;}
        .score-high { color: #2ecc40; font-weight: bold; }
        .score-mid { color: #e67e22; font-weight: bold; }
        .score-low { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    {{ legend|safe }}

    <h2>Live Signals</h2>
    {% if signals %}
    <table>
      <tr>
        <th>Rank</th>
        <th>Symbol</th>
        <th>Score</th>
        <th>Triggers</th>
        <th>Meta</th>
        <th>15m %</th>
        <th>Est Life</th>
        <th>Pump Age</th>
      </tr>
      {% for s in signals %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>{{ s.symbol }}</td>
        <td>
            <span class="{% if s.score >= 10 %}score-high{% elif s.score >= 6 %}score-mid{% else %}score-low{% endif %}">
                {{ "%.2f"|format(s.score) }}
            </span>
        </td>
        <td>{{ s.triggers_str }}</td>
        <td>{{ s.meta }}</td>
        <td>{{ s.change_15m }}</td>
        <td>{{ s.est_life }}</td>
        <td>{{ s.pump_age }}</td>
      </tr>
      {% endfor %}
    </table>
    {% else %}
      <p>No signals available.</p>
    {% endif %}
</body>
</html>
"""

def get_signals():
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE) as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
    else:
        data = []
    return data

@app.route('/')
def dashboard():
    signals = get_signals()
    return render_template_string(DASHBOARD_TEMPLATE, signals=signals, legend=LEGEND_HTML)

@app.route('/api/signals')
def api_signals():
    return jsonify(get_signals())

def live_dashboard(get_data_func=None):
    # For compatibility with your threading usage in main.py
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

if __name__ == "__main__":
    live_dashboard()
