from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import paypalrestsdk

app = Flask(__name__)
app.config['SECRET_KEY'] = 'progress-trading-bot-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trading_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ===== PAYPAL CONFIGURATION =====
# NOTE: Get your credentials from https://developer.paypal.com
paypalrestsdk.configure({
    'mode': 'sandbox',  # Change to 'live' for production
    'client_id': os.environ.get('PAYPAL_CLIENT_ID', 'YOUR_PAYPAL_CLIENT_ID'),
    'client_secret': os.environ.get('PAYPAL_CLIENT_SECRET', 'YOUR_PAYPAL_CLIENT_SECRET')
})

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ===== DATABASE MODELS =====

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    trades = db.relationship('Trade', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'deposit' or 'withdraw'
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='completed')  # 'pending', 'completed', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    action = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ===== LOGIN MANAGER =====

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== DATABASE INITIALIZATION =====
def init_db():
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database init error: {e}")

# ===== ROUTES =====

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Account created! Please login.'}), 201
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'success': True, 'message': 'Login successful!'}), 200
        
        return jsonify({'error': 'Invalid username or password'}), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(10).all()
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', user=current_user, transactions=transactions, trades=trades)

@app.route('/api/deposit', methods=['POST'])
@login_required
def deposit():
    data = request.get_json()
    amount = float(data.get('amount', 0))
    
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400
    
    current_user.balance += amount
    transaction = Transaction(user_id=current_user.id, type='deposit', amount=amount)
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({'success': True, 'balance': current_user.balance, 'message': f'Deposited ${amount:.2f}'}), 200

@app.route('/api/withdraw', methods=['POST'])
@login_required
def withdraw():
    data = request.get_json()
    amount = float(data.get('amount', 0))
    
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400
    if amount > current_user.balance:
        return jsonify({'error': 'Insufficient balance'}), 400
    
    current_user.balance -= amount
    transaction = Transaction(user_id=current_user.id, type='withdraw', amount=amount)
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({'success': True, 'balance': current_user.balance, 'message': f'Withdrew ${amount:.2f}'}), 200

@app.route('/api/paypal_deposit', methods=['POST'])
@login_required
def paypal_deposit():
    """Create PayPal payment for deposit"""
    data = request.get_json()
    amount = float(data.get('amount', 0))
    
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400
    
    try:
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": f"{request.host_url}paypal_return?type=deposit&amount={amount}",
                "cancel_url": f"{request.host_url}paypal_cancel"
            },
            "transactions": [{
                "amount": {
                    "total": f"{amount:.2f}",
                    "currency": "USD"
                },
                "description": f"Progress Trading Bot Deposit - ${amount:.2f}"
            }]
        })
        
        if payment.create():
            # Save pending transaction
            transaction = Transaction(user_id=current_user.id, type='deposit', amount=amount)
            transaction.status = 'pending'
            db.session.add(transaction)
            db.session.commit()
            
            # Get approval URL
            approval_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            
            return jsonify({
                'success': True,
                'approval_url': approval_url,
                'payment_id': payment.id
            }), 200
        else:
            return jsonify({'error': payment.error.get('message', 'Payment creation failed')}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/paypal_withdraw', methods=['POST'])
@login_required
def paypal_withdraw():
    """Create PayPal payout for withdrawal"""
    data = request.get_json()
    amount = float(data.get('amount', 0))
    paypal_email = data.get('paypal_email', '')
    
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400
    if amount > current_user.balance:
        return jsonify({'error': 'Insufficient balance'}), 400
    if not paypal_email:
        return jsonify({'error': 'PayPal email required'}), 400
    
    try:
        payout = paypalrestsdk.Payout({
            "sender_batch_header": {
                "sender_batch_id": f"payout_{current_user.id}_{datetime.utcnow().timestamp()}",
                "email_subject": "Progress Trading Bot Withdrawal"
            },
            "items": [
                {
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": "USD"
                    },
                    "receiver": paypal_email,
                    "note": f"Withdrawal from Progress Trading Bot - ${amount:.2f}"
                }
            ]
        })
        
        if payout.create():
            # Deduct from balance
            current_user.balance -= amount
            transaction = Transaction(user_id=current_user.id, type='withdraw', amount=amount)
            transaction.status = 'completed'
            db.session.add(transaction)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Withdrawal of ${amount:.2f} sent to {paypal_email}',
                'balance': current_user.balance
            }), 200
        else:
            return jsonify({'error': payout.error.get('message', 'Payout failed')}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/paypal_return')
@login_required
def paypal_return():
    """Handle PayPal return after approval"""
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    amount = request.args.get('amount')
    
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            # Update balance
            amount_float = float(amount)
            current_user.balance += amount_float
            
            # Update transaction
            transaction = Transaction.query.filter_by(
                user_id=current_user.id, 
                type='deposit',
                amount=amount_float
            ).order_by(Transaction.created_at.desc()).first()
            
            if transaction:
                transaction.status = 'completed'
            
            db.session.commit()
            
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('dashboard'))
    except Exception as e:
        return redirect(url_for('dashboard'))

@app.route('/paypal_cancel')
@login_required
def paypal_cancel():
    """Handle PayPal cancellation"""
    return redirect(url_for('dashboard'))

@app.route('/api/place_trade', methods=['POST'])
@login_required
def place_trade():
    from trading_bots import fetch_data, strategy
    import pandas as pd
    
    data = request.get_json()
    symbol = data.get('symbol', 'AAPL').upper()
    action = data.get('action', 'buy').lower()
    quantity = float(data.get('quantity', 1))
    
    try:
        # Fetch current price
        df = fetch_data(symbol)
        if df.empty:
            return jsonify({'error': 'Unable to fetch stock data'}), 400
        
        current_price = float(df['close'].iloc[-1])
        total_cost = current_price * quantity
        
        if action == 'buy' and total_cost > current_user.balance:
            return jsonify({'error': 'Insufficient balance for this trade'}), 400
        
        # Execute trade
        if action == 'buy':
            current_user.balance -= total_cost
        else:
            current_user.balance += total_cost
        
        trade = Trade(
            user_id=current_user.id,
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=current_price,
            total=total_cost
        )
        db.session.add(trade)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Trade executed: {action.upper()} {quantity} shares of {symbol} at ${current_price:.2f}',
            'balance': current_user.balance,
            'trade': {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': current_price,
                'total': total_cost
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot_trade', methods=['POST'])
@login_required
def bot_trade():
    """Execute automated bot trades"""
    from trading_bots import fetch_data, strategy
    
    data = request.get_json()
    symbol = data.get('symbol', 'AAPL').upper()
    
    try:
        df = fetch_data(symbol)
        if df.empty:
            return jsonify({'error': 'Unable to fetch stock data'}), 400
        
        df = strategy(df)
        last_position = int(df['position'].iloc[-1])
        current_price = float(df['close'].iloc[-1])
        
        if last_position == 0:
            return jsonify({'signal': 'hold', 'message': 'No trading signal'}), 200
        
        # Determine action
        action = 'buy' if last_position == 1 else 'sell'
        quantity = 1  # Default quantity
        total_cost = current_price * quantity
        
        # Check balance for buy
        if action == 'buy' and total_cost > current_user.balance:
            return jsonify({'error': 'Insufficient balance for bot trade'}), 400
        
        # Execute trade
        if action == 'buy':
            current_user.balance -= total_cost
        else:
            current_user.balance += total_cost
        
        trade = Trade(
            user_id=current_user.id,
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=current_price,
            total=total_cost
        )
        db.session.add(trade)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'signal': action,
            'message': f'Bot executed {action.upper()} signal for {symbol}',
            'balance': current_user.balance,
            'trade': {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': current_price,
                'total': total_cost
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: {e}")
    app.run(debug=True, port=5000)
