import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_telegram_alert(bot_token, chat_id, title, current_price, target_price, url):
    if not bot_token or not chat_id:
        return False, "Telegram Bot Token or Chat ID missing."
        
    endpoint = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    message = (
        f"🚨 <b>PRICE DROP ALERT!</b> 🚨\n\n"
        f"<b>Product:</b> {title}\n"
        f"<b>Current Price:</b> ₹{current_price:,.2f}\n"
        f"<b>Target Price:</b> ₹{target_price:,.2f}\n\n"
        f"🔗 <a href='{url}'>View Deal on Store</a>"
    )
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    
    try:
        res = requests.post(endpoint, json=payload, timeout=10)
        if res.status_code == 200:
            return True, "Telegram notification sent successfully!"
        else:
            data = res.json()
            return False, f"Telegram Error ({res.status_code}): {data.get('description', 'Unknown error')}"
    except Exception as e:
        return False, f"Failed to send Telegram alert: {str(e)}"

def send_email_alert(smtp_server, smtp_port, sender_email, sender_password, recipient_email, title, current_price, target_price, url):
    if not sender_email or not sender_password or not recipient_email:
        return False, "Email configuration missing."
        
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 Price Drop Alert: {title[:30]}..."
        msg["From"] = sender_email
        msg["To"] = recipient_email
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background: #1e293b; padding: 24px; border-radius: 12px; border: 1px solid #334155;">
              <h2 style="color: #38bdf8; margin-top: 0;">🚨 Price Drop Alert!</h2>
              <p style="font-size: 16px;">Good news! A product you are tracking has hit your target price.</p>
              <div style="background: #0f172a; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <p style="margin: 4px 0; font-weight: bold; color: #e2e8f0;">{title}</p>
                <p style="margin: 8px 0 4px 0; font-size: 18px; color: #4ade80;">Current Price: <strong>₹{current_price:,.2f}</strong></p>
                <p style="margin: 0; color: #94a3b8;">Target Price: ₹{target_price:,.2f}</p>
              </div>
              <a href="{url}" style="display: inline-block; background: #0284c7; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View Product Deal</a>
            </div>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, "html"))
        
        server = smtplib.SMTP(smtp_server or "smtp.gmail.com", int(smtp_port or 587))
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Failed to send Email alert: {str(e)}"
