import re
import urllib.parse
import json
import requests
from bs4 import BeautifulSoup

HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'Sec-Ch-Ua': '"Chromium";v="123", "Not:A-Brand";v="8", "Google Chrome";v="123"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
]

def detect_platform(url):
    domain = urllib.parse.urlparse(url).netloc.lower()
    if 'amazon' in domain or 'amzn' in domain:
        return 'Amazon'
    elif 'flipkart' in domain or 'fkrt' in domain:
        return 'Flipkart'
    return 'Other'

def clean_url(url):
    """Normalize Amazon & Flipkart URLs to avoid CAPTCHAs and 403 blocks triggered by tracking queries."""
    platform = detect_platform(url)
    
    if platform == 'Amazon':
        # Extract ASIN (10 alphanumeric chars)
        asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url, re.IGNORECASE)
        if asin_match:
            asin = asin_match.group(1).upper()
            return f"https://www.amazon.in/dp/{asin}"
            
    elif platform == 'Flipkart':
        # Extract item PID or path before tracking params
        parsed = urllib.parse.urlparse(url)
        clean_path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)
        clean_query = ""
        if 'pid' in query_params:
            clean_query = f"?pid={query_params['pid'][0]}"
        return f"https://www.flipkart.com{clean_path}{clean_query}"
        
    return url

def clean_price(price_str):
    if price_str is None:
        return None
    if isinstance(price_str, (int, float)):
        return float(price_str)
        
    price_str = str(price_str).replace(',', '').strip()
    match = re.search(r'\d+(?:\.\d+)?', price_str)
    if match:
        try:
            val = float(match.group(0))
            return val if val > 0 else None
        except ValueError:
            return None
    return None

def scrape_amazon(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Title extraction
    title = None
    title_el = soup.find(id='productTitle')
    if title_el:
        title = title_el.get_text(strip=True)
    elif soup.find('meta', property='og:title'):
        title = soup.find('meta', property='og:title').get('content')

    # Price extraction strategies
    price = None
    
    # Strategy 1: JSON LD metadata
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '{}')
            if isinstance(data, list):
                data = data[0]
            offers = data.get('offers')
            if isinstance(offers, dict) and 'price' in offers:
                price = clean_price(offers['price'])
                if price: break
            elif isinstance(offers, list) and len(offers) > 0 and 'price' in offers[0]:
                price = clean_price(offers[0]['price'])
                if price: break
        except Exception:
            pass

    # Strategy 2: standard price whole / offscreen / apex
    if not price:
        price_whole = soup.find('span', class_='a-price-whole')
        if price_whole:
            price = clean_price(price_whole.get_text())

    if not price:
        offscreen = soup.find('span', class_='a-offscreen')
        if offscreen:
            price = clean_price(offscreen.get_text())

    if not price:
        apex = soup.find('span', id='priceblock_ourprice') or soup.find('span', id='priceblock_dealprice')
        if apex:
            price = clean_price(apex.get_text())

    # Strategy 3: Regex fallback
    if not price:
        match = re.search(r'class="a-price-whole">([^<]+)', html)
        if match:
            price = clean_price(match.group(1))

    # Image extraction
    image_url = None
    img_el = soup.find(id='landingImage') or soup.find(id='imgBlkFront') or soup.find(id='main-image')
    if img_el:
        image_url = img_el.get('src') or img_el.get('data-old-hires')
    elif soup.find('meta', property='og:image'):
        image_url = soup.find('meta', property='og:image').get('content')

    return {
        'title': title or 'Amazon Product',
        'price': price,
        'image_url': image_url or 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=300'
    }

def scrape_flipkart(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Title extraction
    title = None
    title_el = (soup.find('span', class_='B_NuT2') or 
                soup.find('h1') or 
                soup.find('span', class_='VU-LmD') or 
                soup.find('span', class_='_35KyFi'))
    if title_el:
        title = title_el.get_text(strip=True)
    elif soup.find('meta', property='og:title'):
        title = soup.find('meta', property='og:title').get('content')
    elif soup.title:
        title = soup.title.get_text(strip=True).split('Online at Best Price')[0].strip()

    # Price extraction strategies
    price = None
    
    # Strategy 1: JSON LD scripts
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '{}')
            if isinstance(data, list): data = data[0]
            offers = data.get('offers')
            if isinstance(offers, dict) and 'price' in offers:
                price = clean_price(offers['price'])
                if price: break
            elif isinstance(offers, list) and len(offers) > 0 and 'price' in offers[0]:
                price = clean_price(offers[0]['price'])
                if price: break
        except Exception:
            pass

    # Strategy 2: Embedded JSON state objects (Flipkart script state)
    if not price:
        for pattern in [r'"specialPrice":\s*(\d+)', r'"finalPrice":\s*(\d+)', r'"price":\s*(\d+)', r'"displayPrice":\s*(\d+)']:
            matches = re.findall(pattern, html)
            if matches:
                for m in matches:
                    val = clean_price(m)
                    if val and val > 50:
                        price = val
                        break
            if price: break

    # Strategy 3: HTML DOM selectors
    if not price:
        price_el = (soup.find('div', class_='Nx9bqj') or 
                    soup.find('div', class_='_30jeq3') or 
                    soup.find('div', class_='_16JBLd') or
                    soup.find('div', class_='C23O34'))
        if price_el:
            price = clean_price(price_el.get_text())

    # Image extraction
    image_url = None
    img_el = soup.find('img', class_='_396cs4') or soup.find('img', class_='_2r_T1I') or soup.find('img', class_='DslEd2')
    if img_el:
        image_url = img_el.get('src')
    elif soup.find('meta', property='og:image'):
        image_url = soup.find('meta', property='og:image').get('content')

    return {
        'title': title or 'Flipkart Product',
        'price': price,
        'image_url': image_url or 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=300'
    }

def get_product_details(url):
    platform = detect_platform(url)
    target_url = clean_url(url)
    
    headers = HEADERS_LIST[0]
    
    try:
        session = requests.Session()
        response = session.get(target_url, headers=HEADERS_LIST[0], timeout=12)
            
        if response.status_code != 200:
            return {
                'success': False,
                'error': f"HTTP Error {response.status_code}",
                'platform': platform
            }
            
        html = response.text
        if platform == 'Amazon':
            data = scrape_amazon(html)
        elif platform == 'Flipkart':
            data = scrape_flipkart(html)
        else:
            data = scrape_amazon(html)  # Default fallback
            
        data['platform'] = platform
        data['success'] = True if data['price'] is not None else False
        if not data['success']:
            data['error'] = "Could not parse price from page markup"
            
        return data
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'platform': platform
        }

if __name__ == '__main__':
    print("Scraper engine enhanced.")
