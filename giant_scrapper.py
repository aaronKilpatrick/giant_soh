from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as ec
import csv
import time
import sys

def get_default_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless=new")
    # options.add_argument("--start-maximized")
    # options.add_experimental_option("detach", True)
    # options.add_argument("--log-level=3")
    return options

def get_driver_path():
    if sys.platform == "linux":
        return './chromedriver_linx64'
    
def close_modal_by_selector(driver, selector):
    try:
        modal_close_button = WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        modal_close_button.click()
    except TimeoutException:
        print("Modal could not be closed")

def domain_first_visit(visted, url):
    if "giant" in url and visted["giant"] == 0:
        visted["giant"] = 1
        return True
    
    if "liv" in url and visted["liv"] == 0:
        visted["liv"] = 1
        return True

def close_popups_on_load(driver):
    gdrp_button_selector = '.gdprcookie-buttons .btn-primary'
    close_modal_by_selector(driver, gdrp_button_selector)

    modal_button_selector = 'button.needsclick'
    close_modal_by_selector(driver, modal_button_selector)

def get_product_name(driver):
    WebDriverWait(driver, 5).until(ec.title_contains('Australia'))
    page_title = driver.title.split('|')
    page_title = [title.strip() for title in page_title]
    
    if "The Total Race Bike" in page_title or "Ultra-light Endurance Road Bike" in page_title or "Climb higher" in page_title:
        return page_title[1].strip()
    return page_title[0].strip()

def get_element_after_visible(driver, time_wait, selector):
    return WebDriverWait(driver, time_wait).until(ec.visibility_of_element_located((By.CSS_SELECTOR, selector)))

def get_sku(driver):
    return get_element_after_visible(driver, 10,"#selected-partnumber span").text

def get_sku_stock_level(driver):
    stock_level = get_element_after_visible(driver, 10,".stock-info-wrapper .stockinfo")
    return "0" if stock_level.text == 'Contact Store' else "1"

def get_model_stock_levels(driver, soh_list):
    size_buttons = driver.find_elements(By.CSS_SELECTOR, "button.name-and-stockinfo.size")
    product_name = get_product_name(driver)
    for s in size_buttons:
        s.click()
        sku = get_sku(driver)
        stock_level = get_sku_stock_level(driver)
        soh_list.append([sku, product_name, stock_level])
    return soh_list

def get_url_list():
    with open('urls.txt', 'r') as f:
        url_list = f.read().splitlines()
    return url_list

def write_to_csv(soh_list):
    header = ["SKU", "PRODUCT_DESCRIPTION", "STOCK_LEVEL"]
    
    with open("giant_liv_datafeed.csv", "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        
        csv_writer.writerow(header)
        csv_writer.writerows(soh_list)

def progress_indicator(list_length, list_index):
    if list_length == 0: return
    
    list_index = list_index + 1
    
    if list_index == list_length:
        print("\rProgress: 100%", end="", flush=True)
        time.sleep(0.5)
        print("\rProgress: Complete", flush=True)
        return
    
    progress = int(list_index / list_length * 100)
    print(f"\rProgress: {progress}%", end="", flush=True)
    
def main():
    start = time.time()
    page_visted = {
        "liv": 0,
        "giant": 0,
    }
    
    soh_list = []
    product_urls = get_url_list()
    product_urls_len = len(product_urls)
    
    options = get_default_chrome_options()
    service = Service(executable_path=get_driver_path())
    driver = webdriver.Chrome(service=service, options=options)
    
    for i, url in enumerate(product_urls):
        driver.get(url)
        print(url)
        if domain_first_visit(page_visted, url):
            close_popups_on_load(driver)
           
        # wait for the product configurator to be ready
        get_element_after_visible(driver, 10, "#product-configurator")
        colour_btns = driver.find_elements(By.CSS_SELECTOR, ".colors label")
        
        if len(colour_btns) > 0:
            for colour_btn in colour_btns:
                colour_btn.click()
                soh_list = get_model_stock_levels(driver, soh_list)
        else:    
            soh_list = get_model_stock_levels(driver, soh_list)
        
        # progress_indicator(product_urls_len, i)
        
    driver.close()  
    
    write_to_csv(soh_list)
    print(time.time() - start)
if __name__ == "__main__":
    main()
