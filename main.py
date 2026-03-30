import os
import time
from dotenv import load_dotenv
from groq import Groq
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc8RRUAG8n8nPB9dm21m_MxwHQ-JuDnEj7GnvwEkWXykkKFuQ/viewform"

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def generate_answers():
    prompt = """You are filling a daily work journal. Generate realistic, concise answers for the following 4 questions:
1. What were your key tasks for the day?
2. What challenges/problems did you solve today?
3. What challenges/problems were you NOT able to solve today?
4. What is your plan for the next day?

Reply with exactly 4 lines, one answer per line, no numbering or labels."""

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    lines = [l for l in res.choices[0].message.content.strip().split("\n") if l.strip()]
    return lines

def submit_form(answers):
    driver = get_driver()
    wait = WebDriverWait(driver, 20)

    try:
        # Set cookies on google.com domain
        driver.get("https://accounts.google.com")
        time.sleep(2)

        cookie_map = {
            "__Secure-1PSID": os.getenv("GOOGLE_PSID"),
            "__Secure-1PSIDCC": os.getenv("GOOGLE_PSIDCC"),
            "__Secure-1PSIDTS": os.getenv("GOOGLE_PSIDTS"),
            "__Secure-3PSID": os.getenv("GOOGLE_3PSID"),
            "SID": os.getenv("GOOGLE_SID"),
            "HSID": os.getenv("GOOGLE_HSID"),
            "SSID": os.getenv("GOOGLE_SSID"),
            "APISID": os.getenv("GOOGLE_APISID"),
            "SAPISID": os.getenv("GOOGLE_SAPISID"),
            "__Secure-1PAPISID": os.getenv("GOOGLE_PAPISID"),
            "NID": os.getenv("GOOGLE_NID"),
        }

        for name, value in cookie_map.items():
            if value:
                try:
                    driver.add_cookie({"name": name, "value": value, "domain": ".google.com"})
                except Exception:
                    pass

        driver.get(FORM_URL)
        time.sleep(4)

        # Check if we're on the form or sign-in page
        if "sign" in driver.title.lower():
            print("Not authenticated — cookies may have expired.")
            return

        # Check the "Record email" checkbox if unchecked
        try:
            checkbox = driver.find_element(By.XPATH, '//div[@role="checkbox"]')
            if checkbox.get_attribute("aria-checked") == "false":
                checkbox.click()
                time.sleep(1)
        except Exception:
            pass

        # Radio: "It was a working day, and I was present"
        radio = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@data-value="It was a working day, and I was present"]')
        ))
        radio.click()
        time.sleep(2)

        # Click Next
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Next"]')))
        next_btn.click()
        time.sleep(4)

        # Fill text fields
        textareas = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//textarea[@class]')))
        for i, textarea in enumerate(textareas[:4]):
            driver.execute_script("arguments[0].scrollIntoView();", textarea)
            textarea.click()
            time.sleep(0.3)
            textarea.send_keys(answers[i])
            time.sleep(0.5)

        # Handle multi-page: keep clicking Next until Submit appears
        for _ in range(3):
            btns = [b.text.strip() for b in driver.find_elements(By.XPATH, '//span[contains(@class,"NPEfkd")]')]
            if "Submit" in btns:
                break
            if "Next" in btns:
                driver.find_element(By.XPATH, '//span[text()="Next"]').click()
                time.sleep(3)

        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Submit"]')))
        submit_btn.click()
        time.sleep(3)

        print("Form submitted successfully!")

    finally:
        driver.quit()

if __name__ == "__main__":
    answers = generate_answers()
    print("Generated answers:")
    for a in answers:
        print(" -", a)
    submit_form(answers)
