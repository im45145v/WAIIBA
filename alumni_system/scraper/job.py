"""
Scraping job coordinator for the Alumni Management System.

This module coordinates the LinkedIn scraping process:
1. Retrieves alumni records that need updating
2. Scrapes LinkedIn profiles
3. Stores scraped data in the database
4. Uploads PDFs to B2 storage
5. Logs all operations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from ..database.connection import get_db_context
from ..database.crud import (
    create_education_history,
    create_job_history,
    create_scraping_log,
    get_all_alumni,
    update_alumni,
)
from ..database.models import Alumni
from ..storage.b2_client import get_storage_client
from .linkedin_scraper import LinkedInScraper


async def run_scraping_job(
    batch: Optional[str] = None,
    force_update: bool = False,
    max_profiles: int = 100,
    update_threshold_days: int = 180,
) -> dict:
    """
    Run the scraping job for alumni profiles.
    
    Args:
        batch: Filter by specific batch (optional).
        force_update: If True, update all profiles regardless of last scrape time.
        max_profiles: Maximum number of profiles to scrape in this run.
        update_threshold_days: Only update profiles not scraped within this many days.
    
    Returns:
        Dictionary with job statistics.
    """
    stats = {
        "total_processed": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "pdfs_uploaded": 0,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "errors": [],
    }

    try:
        with get_db_context() as db:
            # Get alumni records to process
            alumni_list = get_all_alumni(db, limit=max_profiles, batch=batch)

            # Filter by last scraped date if not forcing update
            threshold_date = datetime.utcnow() - timedelta(days=update_threshold_days)
            
            if not force_update:
                alumni_to_process = [
                    a for a in alumni_list
                    if not a.last_scraped_at or a.last_scraped_at < threshold_date
                ]
            else:
                alumni_to_process = alumni_list

            if not alumni_to_process:
                stats["skipped"] = len(alumni_list)
                stats["completed_at"] = datetime.utcnow().isoformat()
                return stats

            # Initialize scraper
            async with LinkedInScraper() as scraper:
                for alumni in alumni_to_process:
                    stats["total_processed"] += 1
                    
                    if not alumni.linkedin_url and not alumni.linkedin_id:
                        stats["skipped"] += 1
                        continue

                    linkedin_url = alumni.linkedin_url or f"https://www.linkedin.com/in/{alumni.linkedin_id}"
                    start_time = datetime.utcnow()

                    try:
                        # Scrape profile
                        profile_data = await scraper.scrape_profile(linkedin_url)

                        if profile_data:
                            # Update alumni record
                            await _update_alumni_from_profile(db, alumni, profile_data)

                            # Download and store PDF
                            pdf_stored = await _store_profile_pdf(
                                scraper, alumni, linkedin_url, db
                            )
                            if pdf_stored:
                                stats["pdfs_uploaded"] += 1

                            stats["successful"] += 1

                            # Log success
                            duration = (datetime.utcnow() - start_time).seconds
                            create_scraping_log(
                                db,
                                alumni_id=alumni.id,
                                linkedin_url=linkedin_url,
                                status="success",
                                pdf_stored=pdf_stored,
                                duration_seconds=duration,
                            )
                        else:
                            stats["failed"] += 1
                            create_scraping_log(
                                db,
                                alumni_id=alumni.id,
                                linkedin_url=linkedin_url,
                                status="failed",
                                error_message="Failed to scrape profile data",
                                duration_seconds=(datetime.utcnow() - start_time).seconds,
                            )

                    except Exception as e:
                        stats["failed"] += 1
                        stats["errors"].append(f"Alumni {alumni.id}: {str(e)}")
                        create_scraping_log(
                            db,
                            alumni_id=alumni.id,
                            linkedin_url=linkedin_url,
                            status="failed",
                            error_message=str(e),
                            duration_seconds=(datetime.utcnow() - start_time).seconds,
                        )

    except Exception as e:
        stats["errors"].append(f"Job error: {str(e)}")

    stats["completed_at"] = datetime.utcnow().isoformat()
    return stats


async def _update_alumni_from_profile(
    db,
    alumni: Alumni,
    profile_data: dict,
) -> None:
    """
    Update alumni record with scraped profile data.
    
    Args:
        db: Database session.
        alumni: Alumni record to update.
        profile_data: Scraped profile data dictionary.
    """
    # Update basic info
    update_data = {
        "last_scraped_at": datetime.utcnow(),
    }

    if "name" in profile_data:
        update_data["name"] = profile_data["name"]
    if "current_company" in profile_data:
        update_data["current_company"] = profile_data["current_company"]
    if "current_designation" in profile_data:
        update_data["current_designation"] = profile_data["current_designation"]
    if "location" in profile_data:
        update_data["location"] = profile_data["location"]
    if "email" in profile_data:
        update_data["corporate_email"] = profile_data["email"]

    update_alumni(db, alumni.id, **update_data)

    # Update job history
    if "job_history" in profile_data and profile_data["job_history"]:
        # Clear existing job history (optional, might want to merge instead)
        for job in alumni.job_history:
            db.delete(job)
        db.flush()

        # Add new job history
        for job_data in profile_data["job_history"]:
            create_job_history(
                db,
                alumni_id=alumni.id,
                company_name=job_data.get("company_name", "Unknown"),
                designation=job_data.get("designation"),
                location=job_data.get("location"),
                start_date=job_data.get("start_date"),
                end_date=job_data.get("end_date"),
                is_current=job_data.get("is_current", False),
            )

    # Update education history
    if "education_history" in profile_data and profile_data["education_history"]:
        # Clear existing education history
        for edu in alumni.education_history:
            db.delete(edu)
        db.flush()

        # Add new education history
        for edu_data in profile_data["education_history"]:
            create_education_history(
                db,
                alumni_id=alumni.id,
                institution_name=edu_data.get("institution_name", "Unknown"),
                degree=edu_data.get("degree"),
                field_of_study=edu_data.get("field_of_study"),
                start_year=edu_data.get("start_year"),
                end_year=edu_data.get("end_year"),
            )


async def _store_profile_pdf(
    scraper: LinkedInScraper,
    alumni: Alumni,
    linkedin_url: str,
    db,
) -> bool:
    """
    Download and store LinkedIn profile PDF.
    
    Args:
        scraper: LinkedIn scraper instance.
        alumni: Alumni record.
        linkedin_url: LinkedIn profile URL.
        db: Database session.
    
    Returns:
        True if PDF was stored successfully.
    """
    try:
        pdf_bytes = await scraper.download_profile_pdf(linkedin_url)
        if not pdf_bytes:
            return False

        storage_client = get_storage_client()
        linkedin_id = alumni.linkedin_id or alumni.roll_number
        result = storage_client.upload_pdf_bytes(
            pdf_bytes,
            alumni.id,
            linkedin_id,
        )

        # Update alumni record with PDF URL using existing session
        update_alumni(db, alumni.id, linkedin_pdf_url=result["download_url"])

        return True

    except Exception as e:
        print(f"Error storing PDF for alumni {alumni.id}: {e}")
        return False


def run_scraping_job_sync(
    batch: Optional[str] = None,
    force_update: bool = False,
    max_profiles: int = 100,
) -> dict:
    """
    Synchronous wrapper for the scraping job.
    
    Args:
        batch: Filter by specific batch (optional).
        force_update: If True, update all profiles regardless of last scrape time.
        max_profiles: Maximum number of profiles to scrape.
    
    Returns:
        Dictionary with job statistics.
    """
    return asyncio.run(run_scraping_job(batch, force_update, max_profiles))
