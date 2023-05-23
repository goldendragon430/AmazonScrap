from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PIL import Image
from python_anticaptcha import AnticaptchaClient, ImageToTextTask

import csv
import time
def get_basic_information(driver,url):
    driver.get(url)
    wait = WebDriverWait(driver,60)
    tag = wait.until(EC.presence_of_element_located((By.XPATH,"//*[@id='productDetails_techSpec_section_1']")))
    brand_elements =  driver.find_elements(By.CSS_SELECTOR,'#productDetails_techSpec_section_1 > tbody > tr:nth-child(1) > td')
    Brand = brand_elements[0].text
    model_elements =  driver.find_elements(By.CSS_SELECTOR,'#productDetails_techSpec_section_1 > tbody > tr:nth-child(6) > td')
    model = model_elements[0].text
    asin_elements =  driver.find_elements(By.CSS_SELECTOR,'#productDetails_detailBullets_sections1 > tbody > tr:nth-child(1) > td')
    asin = asin_elements[0].text
    return Brand,asin,model 
def output_csv(result):
    with open('result.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        field = ["Brand", "ASIN", "ItemModelNumber", 'Q', 'A', 'Votes','Date','Customer Name']
        writer.writerow(field)
        for row in result:
            writer.writerow([row['Brand'],row['ASIN'],row['ItemModelNumber'],row['Q'],row['A'],row['Votes'],row['Date'],row['Customer Name']])
   
def get_page_count(driver, url):
         
    driver.get(url)
    wait = WebDriverWait(driver,60)
    tag = wait.until(EC.presence_of_element_located((By.XPATH,"//div[@id='askPaginationBar']/ul/li[5]/a")))
    result = tag.get_attribute('href')
    page_count = result.split('/')[7]
    return page_count
def parse_page(driver,brand,asin,item_number, url):
    result = []
    record = {
        'Brand' : brand,
        'ASIN'  : asin,
        'ItemModelNumber' : item_number,
        'Q' : '',
        'A' : '',
        'Votes' : '',
        'Date'  : '',
        'Customer Name' : '' 
    }

    driver.get(url)
    wait = WebDriverWait(driver,60)
    wait.until(EC.presence_of_element_located((By.XPATH,"//*[@class='a-link-normal']")))
    rowContent = driver.find_elements(By.XPATH,"//*[@class='a-section askTeaserQuestions']/div")
    myLink = driver.find_elements(By.PARTIAL_LINK_TEXT, 'see more')
    for item in myLink:
        item.click()
    
    
    for item in rowContent:
        vote_element =  item.find_elements(By.CSS_SELECTOR,'div > div:nth-child(1) > ul > li.label')
        question_element = item.find_elements(By.CSS_SELECTOR,'div > div:nth-child(2) > div:first-child > div > div.a-fixed-left-grid-col.a-col-right > a > span')
        answer_element = item.find_elements(By.CSS_SELECTOR,'div > div:nth-child(2) > div:last-child > div > div:nth-child(2) > span')
        customer_elements = item.find_elements(By.CSS_SELECTOR,'div > div:nth-child(2) > div:last-child > div > div:nth-child(2) > div > div > div:nth-child(2)')
        date_element = item.find_elements(By.CSS_SELECTOR,'div > div:nth-child(2) > div:last-child > div > div:nth-child(2) > div > span')
        
        if len(customer_elements) == 0:
            customer_elements = item.find_elements(By.CSS_SELECTOR,'div > div:nth-child(2) > div:last-child > div > div:nth-child(2)>div>a>div:nth-child(2)>span')
        elif len(customer_elements) > 1:
            customer_elements = [customer_elements[len(customer_elements)-1]]
        
        if len(vote_element) > 0:    
            votes =  vote_element[0].get_attribute('data-count')
        else:
            votes = ''
        if len(question_element) > 0:
            Q = question_element[0].text
        else:
            Q = ''
        if len(answer_element) > 0:
            A = answer_element[0].text.replace('see less','').replace('\n','') 
        else:
            A = ''
        if len(customer_elements) > 0:
            customer = customer_elements[0].text
        else:
            customer = ''
        if len(date_element) > 0:
            Date = date_element[0].text.replace('·','')
        else:
            Date = ''
        row_record = record.copy()
        row_record['Votes'] = votes
        row_record['Q']  = Q
        row_record['A'] = A
        row_record['Customer Name'] = customer
        row_record['Date'] = Date
        result.append(row_record)
    return result
def solve_captcha(driver):
    captcha_fn = "captcha.png"
    element = driver.find_element(By.TAG_NAME, "img") # element name containing the catcha image
    location = element.location
    size = element.size
    driver.save_screenshot("temp.png")

    x = location['x']
    y = location['y']
    w = size['width']
    h = size['height']
    width = x + w
    height = y + h

    im = Image.open('temp.png')
    im = im.crop((int(x), int(y), int(width), int(height)))
    im.save(captcha_fn)

    # request anti-captcha service to decode the captcha

    api_key = '' # api key -> https://anti-captcha.com/
    captcha_fp = open(captcha_fn, 'rb')
    client = AnticaptchaClient(api_key)
    task = ImageToTextTask(captcha_fp)
    job = client.createTask(task)
    job.join()
    text = job.get_captcha_text()    
    print(text)
    input_ele = driver.find_element(By.ID,'captchacharacters')
    input_ele.send_keys(text)
    time.sleep(1)
    submit_btn = driver.find_element(By.TAG_NAME,'button')
    submit_btn.click()
    time.sleep(1)
if __name__ == '__main__':
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    start_url = 'https://www.amazon.com/iSpring-ICEK-Connection-Installation-Reverse/dp/B008H71Q4C?th=1'
    driver.get(start_url)
    # print('Solving Recaptcha...')
    # solve_captcha(driver)
   
    
    
    itemlist =  start_url.split('/')
    page_id =  itemlist[-1].split('?')[0]

    
    Brand,Asin,itemModel = get_basic_information(driver,start_url)
    url = 'https://www.amazon.com/ask/questions/asin/'+page_id+'/1'
    page_count = get_page_count(driver,url)
    result = []
    for i in range(1,int(page_count)):    
        records = parse_page(driver,Brand,Asin,itemModel,'https://www.amazon.com/ask/questions/asin/'+page_id + '/' + str(i))
        result += records
        print( str(int(100 / int(page_count) * i)) + '% done',end='\r')
    print('writing CSV file...')
    output_csv(result)
    driver.close()
