from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message
import requests
import logging

# Initialize the Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.your-email-provider.com'  # e.g., smtp.gmail.com
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-password'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# Store alerts in a list (you can store in a database for production)
alerts = []

@app.route('/set_alert', methods=['POST'])
def set_alert():
    data = request.get_json()
    crypto_symbol = data['crypto_symbol']
    upper_bound = float(data['upper_bound'])
    lower_bound = float(data['lower_bound'])
    email = data['email']
    
    # Save the alert to the list
    alert = {
        'crypto_symbol': crypto_symbol,
        'upper_bound': upper_bound,
        'lower_bound': lower_bound,
        'email': email
    }
    alerts.append(alert)

    # Log the new alert
    app.logger.info(f"New alert set for {crypto_symbol}: Upper bound ${upper_bound}, Lower bound ${lower_bound}")
    
    # Send confirmation email
    msg = Message('Crypto Price Alert Set', sender='your-email@example.com', recipients=[email])
    msg.body = f'You have set an alert for {crypto_symbol}.\nUpper Bound: ${upper_bound}\nLower Bound: ${lower_bound}'
    mail.send(msg)

    return jsonify({"message": "Alert set successfully and confirmation email sent!"}), 200

def check_prices():
    for alert in alerts:
        crypto_symbol = alert['crypto_symbol']
        upper_bound = alert['upper_bound']
        lower_bound = alert['lower_bound']
        email = alert['email']

        # Fetch current price from CoinGecko API
        response = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={crypto_symbol}&vs_currencies=usd')
        data = response.json()
        current_price = data[crypto_symbol]['usd']
        
        # Check if price crosses the thresholds
        if current_price > upper_bound or current_price < lower_bound:
            # Send alert email
            msg = Message(f'{crypto_symbol.capitalize()} Price Alert', sender='your-email@example.com', recipients=[email])
            msg.body = f'The current price of {crypto_symbol} is ${current_price}.\n' \
                       f'It has crossed your alert thresholds (Upper Bound: ${upper_bound}, Lower Bound: ${lower_bound}).'
            mail.send(msg)

            app.logger.info(f"Alert triggered for {crypto_symbol} at ${current_price}")

# Scheduler to check prices every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_prices, trigger="interval", minutes=5)
scheduler.start()

# Start the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
