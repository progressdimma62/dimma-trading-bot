from flask import Flask, render_template, jsonify
import pandas as pd
import numpy as np
from trading_bots import fetch_data, strategy

app = Flask(__name__)

def safe_float(val):
    """Safely convert value to float, handling NaN, Series, and numpy types."""
    try:
        # Handle pandas Series - extract the value
        if isinstance(val, pd.Series):
            val = val.values[0] if len(val) > 0 else None
        # Handle numpy types
        if isinstance(val, (np.floating, np.integer)):
            val = float(val)
        # Handle None and NaN
        if val is None:
            return 0.0
        if isinstance(val, float) and np.isnan(val):
            return 0.0
        return float(val)
    except (ValueError, TypeError, AttributeError, IndexError):
        return 0.0

def safe_int(val):
    """Safely convert value to int, handling Series and numpy types."""
    try:
        # Handle pandas Series - extract the value
        if isinstance(val, pd.Series):
            val = val.values[0] if len(val) > 0 else None
        # Handle numpy types
        if isinstance(val, (np.floating, np.integer)):
            val = int(val)
        # Handle None
        if val is None:
            return 0
        return int(val)
    except (ValueError, TypeError, AttributeError, IndexError):
        return 0

@app.route('/')
def index():
    try:
        symbol = 'AAPL'
        df = fetch_data(symbol)
        if df.empty:
            return render_template('dashboard.html', error='No data fetched', data=None)
        
        df = strategy(df)
        
        # Extract last row values as scalars
        last_close = safe_float(df['close'].iloc[-1])
        last_sma20 = safe_float(df['SMA_20'].iloc[-1])
        last_sma50 = safe_float(df['SMA_50'].iloc[-1])
        last_signal = safe_int(df['signal'].iloc[-1])
        last_position = safe_int(df['position'].iloc[-1])
        
        # Prepare data for frontend
        data = {
            'symbol': symbol,
            'latest_price': last_close,
            'sma_20': last_sma20,
            'sma_50': last_sma50,
            'signal': last_signal,
            'position': last_position,
            'rows': []
        }
        
        # Last 20 rows
        for idx, row in df.tail(20).iterrows():
            data['rows'].append({
                'date': str(idx.date()) if hasattr(idx, 'date') else str(idx),
                'close': safe_float(row['close']),
                'sma_20': safe_float(row['SMA_20']),
                'sma_50': safe_float(row['SMA_50']),
                'signal': safe_int(row['signal']),
                'position': safe_int(row['position'])
            })
        
        return render_template('dashboard.html', error=None, data=data)
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}"
        return render_template('dashboard.html', error=error_msg, data=None)

@app.route('/data')
def get_data():
    try:
        symbol = 'AAPL'
        df = fetch_data(symbol)
        if df.empty:
            return jsonify({'error': 'No data'}), 400
        
        df = strategy(df)
        
        # Get last 50 rows as numpy arrays
        df_tail = df.tail(50)
        
        # Convert to JSON for charts
        chart_data = {
            'dates': [str(idx.date()) if hasattr(idx, 'date') else str(idx) for idx in df_tail.index],
            'prices': [safe_float(x) for x in df_tail['close'].values],
            'sma20': [safe_float(x) for x in df_tail['SMA_20'].values],
            'sma50': [safe_float(x) for x in df_tail['SMA_50'].values]
        }
        return jsonify(chart_data)
    except Exception as e:
        import traceback
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
