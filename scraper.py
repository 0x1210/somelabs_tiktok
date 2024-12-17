# scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import platform
import re
import time
import json
import os

def setup_chrome_options():
    """
    Configure Chrome options for both local and server environment
    """
    chrome_options = Options()
    
    # Basic settings that work across platforms
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Add user agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    return chrome_options

def get_chrome_driver():
    """
    Set up ChromeDriver based on the platform
    """
    try:
        # For local development, try direct Chrome installation
        if platform.system() == 'Darwin':  # macOS
            return webdriver.Chrome(options=setup_chrome_options())
        else:  # Linux (DigitalOcean) or Windows
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=setup_chrome_options())
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        raise

def convert_to_number(text):
    """
    Convert TikTok formatted numbers (like 830.4K, 19.3M) to actual numbers
    """
    if not text:
        return 0
    
    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
    text = text.strip().upper()
    
    if text[-1] in multipliers:
        number = float(text[:-1]) * multipliers[text[-1]]
        return int(number)
    return int(text.replace(',', ''))

def get_tiktok_info(url):
    """
    Scrape TikTok profile information
    """
    profile_data = {
        "tiktok_url": url,
        "name": None,
        "email": None,
        "followers": None,
        "likes": None,
        "website_link": None
    }
    
    driver = None
    try:
        driver = get_chrome_driver()
        print("Browser started successfully...")
        
        driver.set_page_load_timeout(30)
        
        print(f"Loading URL: {url}")
        driver.get(url)
        
        # Initial wait for page load
        time.sleep(10)

        # Try to get name
        try:
            name_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2[data-e2e='user-subtitle'], h1[data-e2e='user-title']"))
            )
            profile_data["name"] = name_element.text
            print(f"Found name: {profile_data['name']}")
        except Exception as e:
            print(f"Could not find name: {e}")

        # Try to get followers and likes
        try:
            followers_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='followers-count']"))
            )
            likes_element = driver.find_element(By.CSS_SELECTOR, "[data-e2e='likes-count']")
            
            profile_data["followers"] = followers_element.text
            profile_data["likes"] = likes_element.text
            print(f"Found followers: {profile_data['followers']}, likes: {profile_data['likes']}")
        except Exception as e:
            print(f"Could not find followers/likes: {e}")

        # Try to get website link
        try:
            website_element = driver.find_element(By.CSS_SELECTOR, "a[data-e2e='user-link']")
            profile_data["website_link"] = website_element.get_attribute("href")
            print(f"Found website: {profile_data['website_link']}")
        except Exception as e:
            print(f"No website link found: {e}")

        # Try to get email from bio with longer waits
        try:
            print("Attempting to extract bio and email...")
            
            # Try to click "more" button if it exists
            try:
                more_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='expand-button']"))
                )
                more_button.click()
                print("Expanded bio by clicking 'more' button")
                time.sleep(3)
            except Exception as e:
                print("No 'more' button found or couldn't click it:", e)
            
            # Wait longer for bio element
            bio_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-bio']"))
            )
            bio_text = bio_element.text
            bio_html = bio_element.get_attribute('innerHTML')
            
            print(f"Found bio text: {bio_text}")
            
            # Look for email in the expanded bio
            email_pattern = r'[\w.+-]+@[\w-]+\.[\w.-]+(?!\S)'
            
            for source in [bio_text, bio_html, driver.page_source]:
                matches = re.findall(email_pattern, source)
                if matches:
                    profile_data["email"] = matches[0]
                    print(f"Found email: {profile_data['email']}")
                    break
                    
            if not profile_data["email"]:
                print("No email found in bio")
                
        except Exception as e:
            print(f"Could not find email: {e}")
            print(f"Bio text was: {bio_text if 'bio_text' in locals() else 'Not available'}")

        return profile_data
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        return profile_data
        
    finally:
        if driver:
            try:
                driver.quit()
                print("Browser closed successfully")
            except Exception as e:
                print(f"Error closing browser: {e}")

def clean_tiktok_url(url):
    """
    Clean TikTok URL to ensure we're using the base profile URL
    """
    url = url.rstrip('/')
    username_match = re.search(r'@[\w\.]+', url)
    if username_match:
        username = username_match.group()
        return f"https://www.tiktok.com/{username}"
    return url

if __name__ == "__main__":
    try:
        url = input("Enter TikTok profile URL (e.g., https://www.tiktok.com/@username): ")
        cleaned_url = clean_tiktok_url(url)
        print(f"\nCleaned URL: {cleaned_url}")
        
        print("\nStarting scraper...")
        result = get_tiktok_info(cleaned_url)
        
        print("\nResult:")
        print(json.dumps(result, indent=2))
        
        with open('tiktok_profile.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("\nData saved to tiktok_profile.json")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")