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

def convert_to_number(text):
    """
    Convert TikTok formatted numbers (like 830.4K, 19.3M) to actual numbers
    Example: '830.4K' -> 830400, '19.3M' -> 19300000
    """
    if not text:
        return 0
    
    # Define multipliers for different suffixes
    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
    text = text.strip().upper()
    
    # Convert numbers with K, M, B suffixes
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
    # Set up Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize dictionary to store profile data
    profile_data = {
        "tiktok_url": url,
        "name": None,
        "email": None,
        "followers": None,
        "likes": None,
        "website_link": None
    }
    
    try:
        # Initialize Chrome driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        print("Browser started...")
        
        # Load the TikTok profile page
        print(f"Loading URL: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Get profile name
        try:
            # Try first selector for name
            title_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2.css-1a4kl8x-H2SubTitle.e1457k4r3"))
            )
            profile_data["name"] = title_container.text
        except:
            try:
                # Try alternate selector for name
                title_container = driver.find_element(By.CSS_SELECTOR, "h2[data-e2e='user-subtitle']")
                profile_data["name"] = title_container.text
            except Exception as e:
                print(f"Could not find name")

        # Get followers and likes counts
        try:
            followers_element = driver.find_element(By.CSS_SELECTOR, "[data-e2e='followers-count']")
            likes_element = driver.find_element(By.CSS_SELECTOR, "[data-e2e='likes-count']")
            
            # Convert formatted numbers to integers
            profile_data["followers"] = convert_to_number(followers_element.text)
            profile_data["likes"] = convert_to_number(likes_element.text)
        except Exception as e:
            print("Could not find followers/likes")

        # Get website link if available
        try:
            website_element = driver.find_element(By.CSS_SELECTOR, "a[data-e2e='user-link']")
            profile_data["website_link"] = website_element.get_attribute("href")
        except:
            print("Could not find website link")

        # Get email from bio
        try:
            print("\nDebug: Starting email extraction...")
            time.sleep(5)  # Wait for page load
            
            # Try multiple methods to get the full bio content
            bio = driver.find_element(By.CSS_SELECTOR, "[data-e2e='user-bio']")
            
            # Try different ways to get the text content
            bio_sources = [
                bio.get_attribute('innerHTML'),  # Get raw HTML
                bio.text,                        # Direct text
                driver.page_source              # Full page source as last resort
            ]
            
            # Look for email in each source
            email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            for source in bio_sources:
                print(f"\nDebug: Checking source: '{source[:100]}...'")  # Print first 100 chars
                match = re.search(email_pattern, source)
                if match:
                    profile_data["email"] = match.group(0)
                    print(f"Debug: Found email: {profile_data['email']}")
                    break

        except Exception as e:
            print(f"Debug: Error finding bio/email: {str(e)}")

        return profile_data
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return profile_data
        
    finally:
        # Always close the browser
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
    # Remove any trailing slash
    url = url.rstrip('/')
    
    # Extract the username part (everything after @)
    username_match = re.search(r'@[\w\.]+', url)
    if username_match:
        username = username_match.group()
        return f"https://www.tiktok.com/{username}"
    
    return url

if __name__ == "__main__":
    # Get TikTok profile URL from user
    url = input("Enter TikTok profile URL (e.g., https://www.tiktok.com/@username): ")
    
    # Clean the URL before processing
    cleaned_url = clean_tiktok_url(url)
    print(f"\nCleaned URL: {cleaned_url}")
    
    # Start the scraping process
    print("\nStarting scraper...")
    result = get_tiktok_info(cleaned_url)
    
    # Print and save results
    print("\nResult:")
    print(json.dumps(result, indent=2))
    
    # Save to JSON file
    with open('tiktok_profile.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\nData saved to tiktok_profile.json")