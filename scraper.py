# scraper.py

# Import required libraries
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import re
import time
import json
import os

def convert_to_number(text):
    """
    Convert TikTok formatted numbers (like 830.4K, 19.3M) to actual numbers
    Example: '830.4K' -> 830400, '19.3M' -> 19300000
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
    Scrape TikTok profile information including:
    - Profile name
    - Email (if available in bio)
    - Follower count
    - Like count
    - Website link (if available)
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Add a user-agent to help avoid detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    profile_data = {
        "tiktok_url": url,
        "name": None,
        "email": None,
        "followers": None,
        "likes": None,
        "website_link": None
    }
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        print("Browser started...")
        
        print(f"Loading URL: {url}")
        driver.get(url)
        
        # Wait longer for the page to load fully
        time.sleep(10)

        # Save page source for debugging
        with open("debug_page_source.html", "w") as f:
            f.write(driver.page_source)

        # Try to locate the user’s name/title
        # Often TikTok shows the username in an h2 or h1 with data-e2e='user-subtitle' or 'user-title'.
        # We try a couple of known selectors:
        try:
            name_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2[data-e2e='user-subtitle'], h1[data-e2e='user-title']"))
            )
            profile_data["name"] = name_element.text
            print(f"Found name: {profile_data['name']}")
        except Exception as e:
            print(f"Could not find name element. Error: {e}")

        # Try to get followers and likes
        try:
            # In newer layouts, followers and likes might be in strong tags with data-e2e attributes
            followers_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='followers-count']"))
            )
            likes_element = driver.find_element(By.CSS_SELECTOR, "[data-e2e='likes-count']")

            profile_data["followers"] = convert_to_number(followers_element.text)
            profile_data["likes"] = convert_to_number(likes_element.text)
            print(f"Found followers: {profile_data['followers']}, likes: {profile_data['likes']}")
        except Exception as e:
            print(f"Could not find followers/likes. Error: {e}")

        # Check for a website link
        try:
            website_element = driver.find_element(By.CSS_SELECTOR, "a[data-e2e='user-link']")
            profile_data["website_link"] = website_element.get_attribute("href")
            print(f"Found website: {profile_data['website_link']}")
        except Exception as e:
            print(f"Could not find website link: {e}")

        # Extract email from bio
        try:
            print("Attempting to extract email from bio...")
            # Wait for bio to appear
            bio_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-bio']"))
            )
            bio_text = bio_element.text
            bio_html = bio_element.get_attribute("innerHTML")

            # Check multiple sources
            sources = [bio_text, bio_html, driver.page_source]
            email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            found_email = None

            for source in sources:
                match = re.search(email_pattern, source)
                if match:
                    found_email = match.group(0)
                    break
            if found_email:
                profile_data["email"] = found_email
                print(f"Found email: {profile_data['email']}")
            else:
                print("No email found in bio.")
        except Exception as e:
            print(f"Error extracting email: {e}")

        return profile_data
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return profile_data
        
    finally:
        # Close the browser
        try:
            driver.quit()
            print("Browser closed.")
        except:
            pass

def clean_tiktok_url(url):
    """
    Clean TikTok URL to ensure we're using the base profile URL
    Converts any TikTok URL (video, etc.) to the main profile URL
    Example: https://www.tiktok.com/@username/video/123456 -> https://www.tiktok.com/@username
    """
    url = url.rstrip('/')
    username_match = re.search(r'@[\w\.]+', url)
    if username_match:
        username = username_match.group()
        return f"https://www.tiktok.com/{username}"
    return url

if __name__ == "__main__":
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