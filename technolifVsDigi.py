import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from datetime import datetime
from rapidfuzz import fuzz

def get_page_content(url, timeout=20, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                print(f"Page loaded successfully: {url}")
                return response.content
            else:
                print(f"Request failed with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            retries += 1
            time.sleep(2)  # Delay before retrying
    return None

def parse_technolife_product(section):
    product_name = section.find('h2').text.strip() if section.find('h2') else "نامشخص"
    price = "نامشخص"
    
    price_tag = section.find('p', class_='text-[22px] font-semiBold leading-5 text-gray-800')
    if price_tag:
        price_text = price_tag.text.replace('تومان', '').replace(',', '').strip()
        # Extract only the number part before any non-numeric characters (e.g., "تومان")
        price = ''.join(filter(str.isdigit, price_text))
    print(f"Technolife product: {product_name}, {price}")
    return product_name, price

def scrape_technolife(base_url):
    page = 1
    all_products = []

    while True:
        url = update_url_query(base_url, {'page': page})
        print(f"Scraping Technolife page: {page}")
        page_content = get_page_content(url)
        if page_content is None:
            break
        
        soup = BeautifulSoup(page_content, 'html.parser')
        sections = soup.find_all('section')
        if not sections:
            break

        for section in sections:
            product_name, price = parse_technolife_product(section)
            all_products.append((product_name, price))

        page += 1
        if page > 20:
            break
        time.sleep(3)  # Increased delay between requests

    return all_products

def update_url_query(url, query_params):
    url_parts = list(urlparse(url))
    query = dict(parse_qs(url_parts[4]))
    query.update(query_params)
    url_parts[4] = urlencode(query, doseq=True)
    return urlunparse(url_parts)

def parse_digikala_product(product_element):
    product_name_tag = product_element.find('h3')
    price_tag = product_element.find('span', class_='price-final')

    product_name = product_name_tag.text.strip() if product_name_tag else "نامشخص"
    price = price_tag.text.replace(',', '').strip() if price_tag else "ناموجود"

    print(f"Digikala product: {product_name}, {price}")
    return product_name, price

def scrape_digikala(base_url, technolife_products):
    page = 1
    all_products = []

    while page <= 20:
        url = f"{base_url}?page={page}&sort=7"
        print(f"Scraping Digikala page: {page}")
        page_content = get_page_content(url)
        if page_content is None:
            break

        soup = BeautifulSoup(page_content, 'html.parser')
        product_elements = soup.find_all('div', class_='product-list_ProductList__item__LiiNI')
        if not product_elements:
            break

        for element in product_elements:
            product_name, price = parse_digikala_product(element)

            # Compare with Technolife products
            matched = False
            for technolife_product_name, technolife_price in technolife_products:
                if fuzz.ratio(product_name, technolife_product_name) >= 85:
                    if technolife_price == "نامشخص" or price == "ناموجود":
                        comparison = "نامشخص"
                    elif int(technolife_price) > int(price):
                        comparison = True
                    else:
                        comparison = False
                    matched = True
                    break
            
            if not matched:
                comparison = False

            all_products.append((product_name, price, comparison))
            print(f"Appended product: {product_name}, {price}, {comparison}")

        page += 1
        time.sleep(3)  # Delay between requests

    return all_products

def save_to_csv(data):
    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f'digiVstechn_{current_date}.csv'
    df = pd.DataFrame(data, columns=['Product Name', 'Price', 'Comparison'])
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"File saved as {filename}")

# URL پایه دیجی‌کالا
digikala_url = 'https://www.digikala.com/search/category-game-console/'

# URL پایه تکنولایف
technolife_url = 'https://www.technolife.ir/product/list/774_947/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%DA%AF%DB%8C%D9%85%DB%8C%D9%86%DA%AF'
technolife_products = scrape_technolife(technolife_url)

# اسکرپ و مقایسه محصولات دیجی‌کالا
all_digikala_products = []
digikala_products = scrape_digikala(digikala_url, technolife_products)
all_digikala_products.extend(digikala_products)

# ذخیره اطلاعات در فایل CSV
save_to_csv(all_digikala_products)
