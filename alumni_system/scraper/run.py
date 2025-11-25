"""
LinkedIn Scraper Runner Script.

This script is designed to be run from the command line or GitHub Actions
to scrape LinkedIn profiles and update the alumni database.

Usage:
    python -m alumni_system.scraper.run [OPTIONS]

Options:
    --batch TEXT          Filter by specific batch
    --max-profiles INT    Maximum profiles to scrape (default: 100)
    --force-update        Force update all profiles regardless of last scrape time
"""

import argparse
import asyncio
import sys
from datetime import datetime

from .job import run_scraping_job


def main():
    """Main entry point for the scraper runner."""
    parser = argparse.ArgumentParser(
        description="Run LinkedIn scraper to update alumni profiles"
    )
    parser.add_argument(
        "--batch",
        type=str,
        default="",
        help="Filter by specific batch (optional)",
    )
    parser.add_argument(
        "--max-profiles",
        type=int,
        default=100,
        help="Maximum number of profiles to scrape",
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Force update all profiles regardless of last scrape time",
    )
    parser.add_argument(
        "--update-threshold-days",
        type=int,
        default=180,
        help="Only update profiles not scraped within this many days",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Alumni LinkedIn Scraper")
    print("=" * 60)
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print(f"Settings:")
    print(f"  - Batch filter: {args.batch or 'All'}")
    print(f"  - Max profiles: {args.max_profiles}")
    print(f"  - Force update: {args.force_update}")
    print(f"  - Update threshold: {args.update_threshold_days} days")
    print("=" * 60)
    
    # Run the scraping job
    try:
        stats = asyncio.run(
            run_scraping_job(
                batch=args.batch if args.batch else None,
                force_update=args.force_update,
                max_profiles=args.max_profiles,
                update_threshold_days=args.update_threshold_days,
            )
        )
        
        # Print results
        print("\nScraping Complete!")
        print("=" * 60)
        print(f"Started at: {stats['started_at']}")
        print(f"Completed at: {stats['completed_at']}")
        print(f"Total processed: {stats['total_processed']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Skipped: {stats['skipped']}")
        print(f"PDFs uploaded: {stats['pdfs_uploaded']}")
        
        if stats['errors']:
            print("\nErrors encountered:")
            for error in stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(stats['errors']) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more errors")
        
        print("=" * 60)
        
        # Exit with error code if there were failures
        if stats['failed'] > 0:
            sys.exit(1)
        
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
