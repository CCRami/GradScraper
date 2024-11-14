import os
import re
from celery import shared_task
import json
from redis import Redis
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from django.conf import settings
from scraperapp.models import Person, Company  # Import your Django models
import smtplib
from email.utils import formataddr
from email.mime.text import MIMEText
import re
import random
from urllib.parse import urlparse
from dotenv import load_dotenv


def verify_email(email):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    load_dotenv()
    email_key = os.getenv("EMAIL_KEY")
    smtp_email = os.getenv("SMTP_EMAIL")
    server.login(smtp_email, email_key) 
    try:
        server.mail(smtp_email)
        code, message = server.rcpt(email) 
        if code == 250:
            print("email success")
            return True
        else:
            print("email failed")
            return False
    except smtplib.SMTPAuthenticationError:
        print("Failed to login")
        return False
    except Exception as e:
        print(f"Error verifying email: {e}")
        return False
    finally:
        server.quit()



@shared_task
def scrape_linkedin_task(st_num, year):
    redis_conn = Redis(host='localhost', port=6379, db=1)

    chrome_driver_path = 'C:/chromedriver-win64/chromedriver.exe'
    service = Service(chrome_driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=1920x1080')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        load_dotenv()
        emaillinkedin = os.getenv("EMAIL")
        password = os.getenv("PASSWORD")
        driver.get("https://www.linkedin.com/login/")
        elementID = driver.find_element(By.ID, 'username')
        elementID.send_keys(emaillinkedin) 
        elementID = driver.find_element(By.ID, 'password')
        elementID.send_keys(password)
        elementID.submit()
        WebDriverWait(driver, 60).until(EC.url_contains('https://www.linkedin.com/feed/'))
        cookies = driver.get_cookies()
        driver.quit()

        options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get('https://www.linkedin.com')

        for cookie in cookies:
            driver.add_cookie(cookie)

        url = f"https://www.linkedin.com/school/ecole-sup%C3%A9rieure-priv%C3%A9e-d'ing%C3%A9nierie-et-de-technologies---esprit/people/?educationEndYear={year}"
        driver.get(url)
        match = re.search(r'educationEndYear=(\d+)', url)
        year = match.group(1) if match else "unknown"

        profiles_per_page = 2  # Number of profiles visible per scroll/page
        #total_scrolls = (st_num * profiles_per_page) + 1  # Calculate the required scrolls
        total_scrolls = 7
        last_height = driver.execute_script("return document.body.scrollHeight")

        for i in range(total_scrolls):
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            driver.execute_script(f'window.scrollTo(0, {scroll_height});')
            
            # Random delay between scrolls
            time.sleep(random.uniform(3, 6))

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        src = driver.page_source
        soup = BeautifulSoup(src, 'lxml')
        uls = soup.find('ul', {'class': 'display-flex list-style-none flex-wrap'})

        if uls is None:
            print("Could not find 'ul' element with class 'display-flex list-style-none flex-wrap'")
            redis_conn.set('scraped_data', json.dumps([]))
        else:
            pr = []
            for li in uls.findAll('li'):
                try:
                    r = li.find('a', {'class': 'app-aware-link'}).get('href')
                    parsed_url = urlparse(r)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    if Person.objects.filter(url__startswith=base_url).exists():
                        print(f"{base_url} already exists in the database. Skipping.")
                        continue
                    pr.append(r)
                except Exception as e:
                    print(f"Error processing 'li' element: {e}")

            random.shuffle(pr)  # Randomize the order of profiles before scraping
            print(f"len(out): {len(pr)}")
            out = []
            new_people_count = 0
            for c, p in enumerate(pr):
                try:
                    driver.get(p)
                    time.sleep(8)
                    src = driver.page_source
                    soup = BeautifulSoup(src, 'lxml')
                    url = p
                    name = soup.find('h1', {'class': 'text-heading-xlarge inline t-24 v-align-middle break-words'}).get_text().strip()

                    # Check if this person already exists in the database
                    if Person.objects.filter(name=name).exists():
                        print(f"{name} already exists in the database. Skipping. len(out): {len(pr)}")
                        remaining_urls = pr[c+1:]
                        random.shuffle(remaining_urls)
                        
                        # Replace the remaining part of the list with the shuffled URLs
                        pr = pr[:c+1] + remaining_urls
                        
                        continue

                    title = soup.find('div', {'class': 'text-body-medium break-words'}).get_text().strip()
                    location = soup.find('span', {'class': 'text-body-small inline t-black--light break-words'}).get_text().strip()
                    dets = soup.find_all('div', {'class': 'inline-show-more-text--is-collapsed'})
                    company_name = dets[0].get_text().strip() if dets else ''
                    img_tag = soup.find('img', {'class': 'presence-entity__image EntityPhoto-circle-1 evi-image lazy-image ember-view'})
                    img_url = img_tag['src'] if img_tag else ''
                    names = name.split(" ", 1)
                    first_name = names[0].lower() if names else ''
                    last_name = names[1].lower() if names else ''
                    first_name = re.sub(r"\s+", "", first_name, flags=re.UNICODE)
                    last_name = re.sub(r"\s+", "", last_name, flags=re.UNICODE)
                    email1 = f"{first_name}.{last_name}@esprit.tn"
                    email2 = f"{last_name}.{first_name}@esprit.tn"
                    if verify_email(email1):
                        email = email1
                    elif verify_email(email2):
                        email = email2
                    else:
                        email = "NA@esprit.tn"
                    person = {"url": url,"email": email,"name": name, "title": title, "location": location, "company": company_name, "img_url": img_url}
                    
                    

                    

                    company, created = Company.objects.get_or_create(name=company_name)

                    Person.objects.update_or_create(
                        name=name,
                        company=company,
                        defaults={
                            'url': url,
                            'email' : email,
                            'title': title,
                            'location': location,
                            'img_url': img_url
                        }
                    )
                    out.append(person)
                    print(f"Scraped data for {name}: {person}")
                    progress_step = len(out)
                    progress_percent = (progress_step / st_num) * 100
                    redis_conn.set('scraped_data', json.dumps(out))
                    redis_conn.set('scraping_progress', json.dumps({'progress': progress_percent, 'step': progress_step, 'total_steps': st_num}))
                    new_people_count += 1

                    if new_people_count >= st_num:
                        break  # Stop when we've added the required number of new people
                except Exception as e:
                    print(f"Error scraping profile {p}: {e}")

            redis_conn.set('scraped_data', json.dumps(out))

    except Exception as e:
        print(f"An error occurred during the scraping process: {e}")
        redis_conn.set('scraped_data', json.dumps([]))

    finally:
        driver.quit()