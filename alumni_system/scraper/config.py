"""
LinkedIn scraper configuration.
Uses environment variables for credentials.
"""

import os


def get_linkedin_credentials() -> dict:
    """
    Get LinkedIn credentials from environment variables.
    
    Required environment variables:
        - LINKEDIN_EMAIL: LinkedIn login email
        - LINKEDIN_PASSWORD: LinkedIn login password
    
    Returns:
        Dictionary containing LinkedIn credentials.
    """
    return {
        "email": os.environ.get("LINKEDIN_EMAIL", ""),
        "password": os.environ.get("LINKEDIN_PASSWORD", ""),
    }


# Scraping settings
HEADLESS_MODE = os.environ.get("SCRAPER_HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.environ.get("SCRAPER_SLOW_MO", "100"))  # milliseconds between actions
TIMEOUT = int(os.environ.get("SCRAPER_TIMEOUT", "30000"))  # page load timeout in ms
MAX_RETRIES = int(os.environ.get("SCRAPER_MAX_RETRIES", "3"))

# Rate limiting
MIN_DELAY_SECONDS = int(os.environ.get("SCRAPER_MIN_DELAY", "5"))
MAX_DELAY_SECONDS = int(os.environ.get("SCRAPER_MAX_DELAY", "15"))

# Profile selectors (may need updates if LinkedIn changes their DOM)
SELECTORS = {
    "login_email": 'input[id="username"]',
    "login_password": 'input[id="password"]',
    "login_button": 'button[type="submit"]',
    "profile_name": 'h1.text-heading-xlarge',
    "profile_headline": 'div.text-body-medium',
    "experience_section": 'section[id="experience"]',
    "education_section": 'section[id="education"]',
    "about_section": 'section[id="about"]',
}
