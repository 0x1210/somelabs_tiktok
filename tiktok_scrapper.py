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

def convert_to_number(text):
    """Convert TikTok formatted numbers (like 830.4K, 19.3M) to actual numbers"""
    if not text:
        return 0
    
    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
    text = text.strip().upper()
    
    if text[-1] in multipliers:
        number = float(text[:-1]) * multipliers[text[-1]]
        return int(number)
    return int(text.replace(',', ''))

def get_tiktok_info(url):
    """Scrape TikTok profile information"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
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
        time.sleep(10)  # Wait for page to load
        
        # Get name
        try:
            title_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2.css-1a4kl8x-H2SubTitle.e1457k4r3"))
            )
            profile_data["name"] = title_container.text
        except:
            try:
                title_container = driver.find_element(By.CSS_SELECTOR, "h2[data-e2e='user-subtitle']")
                profile_data["name"] = title_container.text
            except Exception as e:
                print(f"Could not find name")

        # Get followers and likes
        try:
            followers_element = driver.find_element(By.CSS_SELECTOR, "[data-e2e='followers-count']")
            likes_element = driver.find_element(By.CSS_SELECTOR, "[data-e2e='likes-count']")
            
            profile_data["followers"] = convert_to_number(followers_element.text)
            profile_data["likes"] = convert_to_number(likes_element.text)
        except Exception as e:
            print("Could not find followers/likes")

        # Get website link
        try:
            website_element = driver.find_element(By.CSS_SELECTOR, "a[data-e2e='user-link']")
            profile_data["website_link"] = website_element.get_attribute("href")
        except:
            print("Could not find website link")

        # Get email from bio
        try:
            print("\nDebug: Starting email extraction...")
            time.sleep(5)
            
            # First try to click the "more" button
            try:
                more_button = driver.find_element(By.CSS_SELECTOR, "[data-e2e='user-bio'] button")
                driver.execute_script("arguments[0].click();", more_button)
                time.sleep(5)  # Wait for bio to expand
                print("Debug: Clicked more button")
            except Exception as e:
                print(f"Debug: No more button found or already expanded: {str(e)}")
            
            # Now get the expanded bio text
            bio = driver.find_element(By.CSS_SELECTOR, "[data-e2e='user-bio']")
            bio_text = bio.text
            print(f"Debug: Bio text after expansion: '{bio_text}'")
            
            # Extract email using regex
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            match = re.search(email_pattern, bio_text)
            if match:
                profile_data["email"] = match.group(0)
                print(f"Debug: Found email: {profile_data['email']}")
            else:
                # Try getting innerHTML as fallback
                bio_html = bio.get_attribute('innerHTML')
                print(f"Debug: Trying innerHTML: '{bio_html}'")
                match = re.search(email_pattern, bio_html)
                if match:
                    profile_data["email"] = match.group(0)
                    print(f"Debug: Found email in innerHTML: {profile_data['email']}")
                else:
                    print("Debug: No email found in bio text or innerHTML")

        except Exception as e:
            print(f"Debug: Error in email extraction: {str(e)}")

        return profile_data
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return profile_data
        
    finally:
        try:
            driver.quit()
            print("Browser closed.")
        except:
            pass

if __name__ == "__main__":
    url = input("Enter TikTok profile URL (e.g., https://www.tiktok.com/@username): ")
    print("\nStarting scraper...")
    result = get_tiktok_info(url)
    
    print("\nResult:")
    print(json.dumps(result, indent=2))
    
    with open('tiktok_profile.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\nData saved to tiktok_profile.json")