"""
LinkedIn profile scraper using Playwright.

This module provides functionality to scrape LinkedIn profiles
and extract alumni information such as name, current company,
email, job history, and education.

IMPORTANT: Web scraping LinkedIn may violate their Terms of Service.
Use responsibly and ensure compliance with applicable laws and policies.
"""

import asyncio
import random
import re
from datetime import datetime
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .config import (
    HEADLESS_MODE,
    MAX_DELAY_SECONDS,
    MAX_RETRIES,
    MIN_DELAY_SECONDS,
    SELECTORS,
    SLOW_MO,
    TIMEOUT,
    get_linkedin_credentials,
)


class LinkedInScraper:
    """
    Scraper for extracting alumni information from LinkedIn profiles.
    
    Uses Playwright for browser automation and supports:
    - Profile data extraction (name, headline, location)
    - Job history extraction
    - Education history extraction
    - PDF download of profiles
    """

    def __init__(self):
        """Initialize the LinkedIn scraper."""
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._logged_in = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Start the browser and initialize context."""
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch(
            headless=HEADLESS_MODE,
            slow_mo=SLOW_MO,
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(TIMEOUT)

    async def close(self) -> None:
        """Close the browser and cleanup resources."""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()

    async def _random_delay(self) -> None:
        """Add a random delay to avoid detection."""
        delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
        await asyncio.sleep(delay)

    async def login(self) -> bool:
        """
        Log in to LinkedIn using credentials from environment variables.
        
        Returns:
            True if login successful, False otherwise.
        """
        if self._logged_in:
            return True

        credentials = get_linkedin_credentials()
        if not credentials["email"] or not credentials["password"]:
            raise ValueError("LinkedIn credentials not configured in environment variables")

        try:
            # Navigate to login page
            await self._page.goto("https://www.linkedin.com/login")
            await self._random_delay()

            # Fill in credentials
            await self._page.fill(SELECTORS["login_email"], credentials["email"])
            await self._page.fill(SELECTORS["login_password"], credentials["password"])

            # Click login button
            await self._page.click(SELECTORS["login_button"])
            await self._page.wait_for_load_state("networkidle")

            # Check if login was successful
            if "feed" in self._page.url or "mynetwork" in self._page.url:
                self._logged_in = True
                return True

            # Check for security verification or error
            if "checkpoint" in self._page.url:
                raise Exception("LinkedIn security verification required")

            return False

        except Exception as e:
            print(f"Login failed: {e}")
            return False

    async def scrape_profile(self, linkedin_url: str) -> Optional[dict]:
        """
        Scrape a LinkedIn profile and extract relevant information.
        
        Args:
            linkedin_url: URL of the LinkedIn profile to scrape.
        
        Returns:
            Dictionary containing extracted profile data, or None if failed.
        """
        if not self._logged_in:
            if not await self.login():
                raise Exception("Failed to login to LinkedIn")

        for attempt in range(MAX_RETRIES):
            try:
                await self._random_delay()
                await self._page.goto(linkedin_url)
                await self._page.wait_for_load_state("networkidle")

                # Extract profile data
                profile_data = {
                    "linkedin_url": linkedin_url,
                    "scraped_at": datetime.utcnow().isoformat(),
                }

                # Extract basic info
                profile_data.update(await self._extract_basic_info())

                # Extract experience
                profile_data["job_history"] = await self._extract_experience()

                # Extract education
                profile_data["education_history"] = await self._extract_education()

                # Extract contact info if available
                profile_data.update(await self._extract_contact_info())

                return profile_data

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    await self._random_delay()
                continue

        return None

    async def _extract_basic_info(self) -> dict:
        """Extract basic profile information."""
        data = {}

        try:
            # Name
            name_element = await self._page.query_selector(SELECTORS["profile_name"])
            if name_element:
                data["name"] = await name_element.inner_text()

            # Headline/Current position
            headline_element = await self._page.query_selector(SELECTORS["profile_headline"])
            if headline_element:
                data["headline"] = await headline_element.inner_text()

            # Location
            location_selector = 'span.text-body-small.inline.t-black--light.break-words'
            location_element = await self._page.query_selector(location_selector)
            if location_element:
                data["location"] = await location_element.inner_text()

            # Extract current company from headline
            if "headline" in data:
                headline = data["headline"]
                if " at " in headline.lower():
                    parts = headline.split(" at ", 1)
                    if len(parts) == 2:
                        data["current_designation"] = parts[0].strip()
                        data["current_company"] = parts[1].strip()

        except Exception as e:
            print(f"Error extracting basic info: {e}")

        return data

    async def _extract_experience(self) -> list[dict]:
        """Extract work experience history."""
        experiences = []

        try:
            # Navigate to experience section or click "Show all" if needed
            experience_section = await self._page.query_selector(SELECTORS["experience_section"])
            if not experience_section:
                return experiences

            # Get all experience items
            exp_items = await experience_section.query_selector_all('li.artdeco-list__item')

            for item in exp_items[:10]:  # Limit to prevent excessive scraping
                try:
                    exp_data = {}

                    # Company name
                    company_el = await item.query_selector('span.t-14.t-normal')
                    if company_el:
                        exp_data["company_name"] = await company_el.inner_text()

                    # Job title
                    title_el = await item.query_selector('span.t-14.t-bold')
                    if title_el:
                        exp_data["designation"] = await title_el.inner_text()

                    # Duration
                    duration_el = await item.query_selector('span.t-14.t-normal.t-black--light')
                    if duration_el:
                        duration_text = await duration_el.inner_text()
                        exp_data["duration"] = duration_text
                        # Parse dates from duration
                        dates = self._parse_dates(duration_text)
                        exp_data.update(dates)

                    # Location
                    location_el = await item.query_selector('span.t-14.t-normal.t-black--light:nth-child(2)')
                    if location_el:
                        exp_data["location"] = await location_el.inner_text()

                    if exp_data:
                        experiences.append(exp_data)

                except Exception as e:
                    print(f"Error extracting experience item: {e}")
                    continue

        except Exception as e:
            print(f"Error extracting experience: {e}")

        return experiences

    async def _extract_education(self) -> list[dict]:
        """Extract education history."""
        education = []

        try:
            education_section = await self._page.query_selector(SELECTORS["education_section"])
            if not education_section:
                return education

            edu_items = await education_section.query_selector_all('li.artdeco-list__item')

            for item in edu_items[:5]:  # Limit results
                try:
                    edu_data = {}

                    # Institution name
                    inst_el = await item.query_selector('span.t-14.t-bold')
                    if inst_el:
                        edu_data["institution_name"] = await inst_el.inner_text()

                    # Degree
                    degree_el = await item.query_selector('span.t-14.t-normal')
                    if degree_el:
                        degree_text = await degree_el.inner_text()
                        if "," in degree_text:
                            parts = degree_text.split(",", 1)
                            edu_data["degree"] = parts[0].strip()
                            edu_data["field_of_study"] = parts[1].strip()
                        else:
                            edu_data["degree"] = degree_text

                    # Years
                    years_el = await item.query_selector('span.t-14.t-normal.t-black--light')
                    if years_el:
                        years_text = await years_el.inner_text()
                        years = self._parse_years(years_text)
                        edu_data.update(years)

                    if edu_data:
                        education.append(edu_data)

                except Exception as e:
                    print(f"Error extracting education item: {e}")
                    continue

        except Exception as e:
            print(f"Error extracting education: {e}")

        return education

    async def _extract_contact_info(self) -> dict:
        """Extract contact information from profile."""
        data = {}

        try:
            # Click on contact info link
            contact_link = await self._page.query_selector('a[id="top-card-text-details-contact-info"]')
            if contact_link:
                await contact_link.click()
                await asyncio.sleep(2)

                # Extract email if visible
                email_section = await self._page.query_selector('section.ci-email')
                if email_section:
                    email_el = await email_section.query_selector('a')
                    if email_el:
                        email = await email_el.inner_text()
                        data["email"] = email

                # Close modal
                close_button = await self._page.query_selector('button[aria-label="Dismiss"]')
                if close_button:
                    await close_button.click()

        except Exception as e:
            print(f"Error extracting contact info: {e}")

        return data

    def _parse_dates(self, duration_text: str) -> dict:
        """Parse start and end dates from duration text."""
        dates = {}

        try:
            # Pattern: "Jan 2020 - Present" or "Jan 2020 - Dec 2023"
            match = re.search(
                r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|Present)',
                duration_text,
                re.IGNORECASE
            )
            if match:
                start_str = match.group(1)
                end_str = match.group(2)

                try:
                    dates["start_date"] = datetime.strptime(start_str, "%b %Y").isoformat()
                except ValueError:
                    pass

                if end_str.lower() != "present":
                    try:
                        dates["end_date"] = datetime.strptime(end_str, "%b %Y").isoformat()
                    except ValueError:
                        pass
                else:
                    dates["is_current"] = True

        except Exception:
            pass

        return dates

    def _parse_years(self, years_text: str) -> dict:
        """Parse start and end years from education years text."""
        years = {}

        try:
            # Pattern: "2018 - 2022" or "2020"
            match = re.search(r'(\d{4})\s*[-–]\s*(\d{4})', years_text)
            if match:
                years["start_year"] = int(match.group(1))
                years["end_year"] = int(match.group(2))
            else:
                # Single year
                match = re.search(r'(\d{4})', years_text)
                if match:
                    years["end_year"] = int(match.group(1))

        except Exception:
            pass

        return years

    async def download_profile_pdf(self, linkedin_url: str) -> Optional[bytes]:
        """
        Download LinkedIn profile as PDF.
        
        Args:
            linkedin_url: URL of the LinkedIn profile.
        
        Returns:
            PDF content as bytes, or None if failed.
        """
        if not self._logged_in:
            if not await self.login():
                raise Exception("Failed to login to LinkedIn")

        try:
            await self._random_delay()
            await self._page.goto(linkedin_url)
            await self._page.wait_for_load_state("networkidle")

            # Generate PDF from page
            pdf_bytes = await self._page.pdf(
                format="A4",
                print_background=True,
                margin={
                    "top": "1cm",
                    "right": "1cm",
                    "bottom": "1cm",
                    "left": "1cm",
                },
            )

            return pdf_bytes

        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return None


async def scrape_linkedin_profile(linkedin_url: str) -> Optional[dict]:
    """
    Convenience function to scrape a single LinkedIn profile.
    
    Args:
        linkedin_url: URL of the LinkedIn profile.
    
    Returns:
        Dictionary containing profile data, or None if failed.
    """
    async with LinkedInScraper() as scraper:
        return await scraper.scrape_profile(linkedin_url)


async def scrape_multiple_profiles(linkedin_urls: list[str]) -> list[dict]:
    """
    Scrape multiple LinkedIn profiles.
    
    Args:
        linkedin_urls: List of LinkedIn profile URLs.
    
    Returns:
        List of dictionaries containing profile data.
    """
    results = []

    async with LinkedInScraper() as scraper:
        for url in linkedin_urls:
            profile_data = await scraper.scrape_profile(url)
            if profile_data:
                results.append(profile_data)

    return results
