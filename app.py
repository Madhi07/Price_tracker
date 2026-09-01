import os
from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import database
import scraper
import notifier

app = Flask(__name__)

# Initialize database
try:
    database.init_db()
except Exception as e:
    print(f"Database init warning: {e}")

# Scheduler initialization
scheduler = BackgroundScheduler(daemon=True, timezone="UTC")

def check_all_prices():
    """Background task to check prices of all active products."""
    print("[Background Scheduler] Running automated price checks...")
    try:
        products = database.get_all_products()
        settings = database.get_settings()
        
        for prod in products:
            if prod['status'] != 'active':
                continue
                
            print(f"Scraping product ID {prod['id']}: {prod['url']}")
            res = scraper.get_product_details(prod['url'])
            
            if res.get('success') and res.get('price'):
                new_price = res['price']
                database.update_product_price(prod['id'], new_price, title=res.get('title'), image_url=res.get('image_url'))
                
                # Check if price dropped below target
                target_price = prod['target_price']
                if new_price <= target_price:
                    print(f"PRICE ALERT for {prod['title']}! Current: {new_price}, Target: {target_price}")
                    
                    # Send Telegram Alert
                    bot_token = settings.get('telegram_bot_token')
                    chat_id = settings.get('telegram_chat_id')
                    if bot_token and chat_id:
                        notifier.send_telegram_alert(
                            bot_token, chat_id, prod['title'], new_price, target_price, prod['url']
                        )
                        
                    # Send Email Alert
                    if settings.get('email_alerts_enabled') == 'true':
                        notifier.send_email_alert(
                            settings.get('smtp_server'),
                            settings.get('smtp_port'),
                            settings.get('smtp_email'),
                            settings.get('smtp_password'),
                            settings.get('recipient_email'),
                            prod['title'], new_price, target_price, prod['url']
                        )
            else:
                print(f"Failed to scrape product ID {prod['id']}: {res.get('error')}")
    except Exception as err:
        print(f"Error in background check_all_prices: {err}")

# Configure scheduler job
try:
    settings = database.get_settings()
    interval_hours = int(settings.get('check_interval_hours', 4))
    scheduler.add_job(check_all_prices, 'interval', hours=interval_hours, id='price_check_job', replace_existing=True)
    scheduler.start()
except Exception as sched_err:
    print(f"Scheduler startup warning: {sched_err}")

@app.route('/')
def index():
    try:
        database.init_db()
        return render_template('index.html')
    except Exception as e:
        return f"<h3>Application Initializing...</h3><p>{str(e)}</p>", 500

@app.route('/api/products', methods=['GET'])
def get_products():
    products = database.get_all_products()
    return jsonify({'success': True, 'products': products})

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json or {}
    url = data.get('url', '').strip()
    target_price = data.get('target_price')
    
    if not url:
        return jsonify({'success': False, 'error': 'Product URL is required.'}), 400
        
    try:
        target_price = float(target_price)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid target price.'}), 400
        
    # Scrape initial product info
    scrape_res = scraper.get_product_details(url)
    
    platform = scrape_res.get('platform', 'Unknown')
    title = scrape_res.get('title') or (f"{platform} Product")
    current_price = scrape_res.get('price')
    image_url = scrape_res.get('image_url')
    
    try:
        prod_id = database.add_product(
            title=title,
            url=url,
            platform=platform,
            target_price=target_price,
            current_price=current_price,
            image_url=image_url
        )
        new_product = database.get_product(prod_id)
        return jsonify({'success': True, 'product': new_product, 'scrape_info': scrape_res})
    except Exception as e:
        return jsonify({'success': False, 'error': f"Database insertion failed (URL may already be tracked): {str(e)}"}), 400

@app.route('/api/products/<int:prod_id>', methods=['DELETE'])
def delete_product(prod_id):
    database.delete_product(prod_id)
    return jsonify({'success': True, 'message': 'Product removed.'})

@app.route('/api/products/<int:prod_id>/check', methods=['POST'])
def check_product(prod_id):
    prod = database.get_product(prod_id)
    if not prod:
        return jsonify({'success': False, 'error': 'Product not found.'}), 404
        
    res = scraper.get_product_details(prod['url'])
    if res.get('success') and res.get('price'):
        new_price = res['price']
        database.update_product_price(prod_id, new_price, title=res.get('title'), image_url=res.get('image_url'))
        
        # Check alert trigger
        alert_sent = False
        settings = database.get_settings()
        if new_price <= prod['target_price']:
            bot_token = settings.get('telegram_bot_token')
            chat_id = settings.get('telegram_chat_id')
            if bot_token and chat_id:
                notifier.send_telegram_alert(
                    bot_token, chat_id, prod['title'], new_price, prod['target_price'], prod['url']
                )
                alert_sent = True
                
        updated_prod = database.get_product(prod_id)
        return jsonify({'success': True, 'product': updated_prod, 'alert_sent': alert_sent})
    else:
        return jsonify({'success': False, 'error': res.get('error', 'Scrape failed')}), 400

@app.route('/api/products/check-all', methods=['POST'])
def check_all_manual():
    check_all_prices()
    return jsonify({'success': True, 'message': 'Manual check completed for all items.'})

@app.route('/api/products/<int:prod_id>/history', methods=['GET'])
def get_history(prod_id):
    history = database.get_product_history(prod_id)
    return jsonify({'success': True, 'history': history})

@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = database.get_settings()
    return jsonify({'success': True, 'settings': settings})

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.json or {}
    database.update_settings(data)
    
    # Reconfigure scheduler if interval changed
    if 'check_interval_hours' in data:
        try:
            hrs = int(data['check_interval_hours'])
            scheduler.reschedule_job('price_check_job', trigger='interval', hours=hrs)
        except Exception:
            pass
            
    return jsonify({'success': True, 'message': 'Settings updated successfully.'})

@app.route('/api/test-notification', methods=['POST'])
def test_notification():
    data = request.json or {}
    settings = database.get_settings()
    
    bot_token = data.get('telegram_bot_token') or settings.get('telegram_bot_token')
    chat_id = data.get('telegram_chat_id') or settings.get('telegram_chat_id')
    
    if not bot_token or not chat_id:
        return jsonify({'success': False, 'error': 'Please enter both Telegram Bot Token and Chat ID.'}), 400
        
    ok, msg = notifier.send_telegram_alert(
        bot_token, chat_id,
        "Test Product - Smart Price Tracker",
        999.0, 1000.0,
        "https://amazon.in"
    )
    return jsonify({'success': ok, 'message': msg})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
