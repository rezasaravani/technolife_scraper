import requests
from lxml import html
import pandas as pd
import time
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from datetime import datetime

def get_page_content(url, timeout=20, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return html.fromstring(response.content)
            else:
                print(f"Request failed with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            retries += 1
            time.sleep(2)  # Delay before retrying
    return None

def parse_product_section(section):
    product_name_xpath = './/h2/text()'
    price_xpath = './/div[@class=" flex justify-end pb-[42px] pl-4"]/p/text()'

    product_name = section.xpath(product_name_xpath)[0].strip() if section.xpath(product_name_xpath) else "نامشخص"
    print(product_name)
    
    available = False
    price = "نامشخص"
    
    price_tags = section.xpath(price_xpath)
    if price_tags:
        price = price_tags[0].replace(',', '').replace('تومان', '').strip()


    available_tag = section.xpath('.//span')
    if available_tag and any("تومان" in span.text_content() for span in available_tag):
        available = True
    elif section.xpath('.//p') and any("ناموجود" in p.text_content() for p in section.xpath('.//p')):
        available = False
    
    print(price)

    return product_name, available, price

def scrape_page(url):
    tree = get_page_content(url)
    if not tree:
        return None, False
    
    sections = tree.xpath('//section')
    if not sections:
        return None, False

    products = []
    for section in sections:
        product_name, available, price = parse_product_section(section)
        products.append((product_name, available, price))

    return products, True

def update_url_query(url, query_params):
    url_parts = list(urlparse(url))
    query = dict(parse_qs(url_parts[4]))
    query.update(query_params)
    url_parts[4] = urlencode(query, doseq=True)
    return urlunparse(url_parts)

def scrape_website(base_url):
    page = 1
    all_products = []

    while True:
        url = update_url_query(base_url, {'page': page})
        print(f"Scraping page: {page}")
        products, has_sections = scrape_page(url)
        if products:
            all_products.extend(products)
        if not has_sections:
            break
        page += 1
        time.sleep(3)  # Increased delay between requests

    return all_products

def save_to_csv(data):
    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f'products_{current_date}.csv'
    df = pd.DataFrame(data, columns=['Product Name', 'Available', 'Price'])
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"File saved as {filename}")

# URL پایه فروشگاه
base_url = 'https://www.technolife.ir/product/list/774_947/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%DA%AF%DB%8C%D9%85%DB%8C%D9%86%DA%AF'
all_products = scrape_website(base_url)

# ذخیره اطلاعات در فایل CSV
save_to_csv(all_products)
