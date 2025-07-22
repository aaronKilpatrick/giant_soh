from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import csv

def get_default_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)
    # options.add_argument("--log-level=3")
    return options
    
def close_modal_by_selector(driver, selector):
    try:
        modal_close_button = WebDriverWait(driver, 2).until(ec.element_to_be_clickable((By.CSS_SELECTOR, selector)))
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
    return driver.title.split('|')[0].strip()

def get_element_after_visible(driver, time_wait, selector):
    return WebDriverWait(driver, time_wait).until(ec.visibility_of_element_located((By.CSS_SELECTOR, selector)))

def get_sku(driver):
    return get_element_after_visible(driver, 2,"#selected-partnumber span").text

def get_sku_stock_level(driver):
    stock_level = get_element_after_visible(driver, 2,".stock-info-wrapper .stockinfo")
    return "0" if stock_level.text == 'Contact Store' else "1"

def get_model_stock_levels(driver, soh_list):
    size_buttons = driver.find_elements(By.CSS_SELECTOR, "button.name-and-stockinfo.size")
    product_name = get_product_name(driver)
    for s in size_buttons:
        s.click()
        size = s.text
        sku = get_sku(driver)
        stock_level = get_sku_stock_level(driver)
        print(sku + size + product_name)
        soh_list.append([sku, product_name, size, stock_level])
    return soh_list

def get_url_list():
    with open('urls.txt', 'r') as f:
        url_list = f.read().splitlines()
    return url_list

def write_to_csv(soh_list):
    header = ["SKU", "PRODUCT_DESCRIPTION", "SIZE", "STOCK_LEVEL"]
    
    with open("giant_liv_datafeed.csv", "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        
        csv_writer.writerow(header)
        csv_writer.writerows(soh_list)

def main():
    soh_list = []
    page_visted = {
        "liv": 0,
        "giant": 0,
    }
    product_urls = get_url_list()
    options = get_default_chrome_options()
    driver = webdriver.Chrome(options=options)
    
    for url in product_urls:
        # options = get_default_chrome_options()
        # driver = webdriver.Chrome(options=options)
        driver.get(url)
        if domain_first_visit(page_visted, url):
            close_popups_on_load(driver)
            
        print(url)
        # wait for the product configurator to be ready
        get_element_after_visible(driver, 10, "#product-configurator")
        colours = driver.find_elements(By.CSS_SELECTOR, ".colors label")
        if len(colours) > 0:
            for colour in colours:
                colour.click()
                soh_list = get_model_stock_levels(driver, soh_list)
        else:    
            soh_list = get_model_stock_levels(driver, soh_list)
    
    driver.close()  
    
    write_to_csv(soh_list)

if __name__ == "__main__":
    main()
