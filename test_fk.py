import requests
import re
from bs4 import BeautifulSoup

url = "https://www.flipkart.com/motorola-edge-60-pro-pantone-sparkling-grape-256-gb/p/itm26341e4d28553?pid=MOBH9C9JFZTVJP87"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
    'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1'
}

r = requests.get(url, headers=headers)
print("STATUS:", r.status_code)

soup = BeautifulSoup(r.text, 'html.parser')

# Check all elements with currency symbol or price classes
print("Title:", soup.title.get_text() if soup.title else "No title")

# Print any div/span containing numbers with commas like 32,999 or 33,999
text_matches = re.findall(r'₹\s*[\d,]+', r.text)
print("Currency Matches count:", len(text_matches))

# Find price classes
classes = ['Nx9bqj', '_30jeq3', '_16JBLd', 'C23O34', '_35KyFi', 'VU-LmD']
for c in classes:
    els = soup.find_all(class_=c)
    if els:
        print(f"Class {c}: {[el.get_text() for el in els]}")

# Find any JSON price pattern
json_prices = re.findall(r'"(?:specialPrice|finalPrice|price|amount|value)":\s*(\d+)', r.text)
print("JSON prices found:", json_prices[:10])

# Find LD+JSON
for s in soup.find_all('script', type='application/ld+json'):
    print("LD+JSON:", s.string[:300])
