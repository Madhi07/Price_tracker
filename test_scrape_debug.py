import re
import json
from bs4 import BeautifulSoup

def inspect_flipkart():
    html = open('test_flipkart.html', encoding='utf-8').read()
    soup = BeautifulSoup(html, 'html.parser')
    
    print("=== FLIPKART SCRAPE TEST ===")
    print("Title:", soup.title.string if soup.title else "No title")
    
    # 1. ld+json scripts
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '{}')
            print("Found LD+JSON:", data.get('@type'))
            if 'offers' in data:
                print("Offers Price:", data['offers'].get('price'))
        except Exception as e:
            pass
            
    # 2. JSON regexes
    prices = re.findall(r'"price":\s*(\d+)', html)
    print("Regex 'price':", prices[:5])
    
    special_prices = re.findall(r'"specialPrice":\s*(\d+)', html)
    print("Regex 'specialPrice':", special_prices[:5])

def inspect_amazon():
    html = open('test_amazon.html', encoding='utf-8').read()
    soup = BeautifulSoup(html, 'html.parser')
    
    print("\n=== AMAZON SCRAPE TEST ===")
    print("Title:", soup.find(id='productTitle').get_text(strip=True) if soup.find(id='productTitle') else "No title")
    
    # 1. ld+json scripts
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '{}')
            print("Found LD+JSON:", data.get('@type'))
        except Exception:
            pass

    # 2. Price Whole
    pw = soup.find_all('span', class_='a-price-whole')
    print("a-price-whole count:", len(pw))
    if pw:
        print("First a-price-whole:", pw[0].get_text())

if __name__ == '__main__':
    inspect_flipkart()
    inspect_amazon()
