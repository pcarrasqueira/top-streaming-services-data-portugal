#!/usr/bin/env python3
"""
Diagnostic script to check the current FlixPatrol HTML structure
and test the scraping functionality.

Usage:
    python diagnose_flixpatrol.py

This will help identify what changes FlixPatrol made to their website
and verify that the scraper can handle them correctly.
"""
import logging
import sys

import requests
from bs4 import BeautifulSoup

from top_pt_stream_services import scrape_top10

# Configure logging to show detailed information
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


def diagnose_page(url, section_title):
    """Diagnose the structure of a FlixPatrol page."""
    print(f"\n{'='*80}")
    print(f"Diagnosing: {url}")
    print(f"Expected section: {section_title}")
    print("=" * 80)

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Cookie": "_nss=1",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"\nStatus code: {response.status_code}")

        if response.status_code != 200:
            print(f"ERROR: Failed to retrieve page")
            return

        soup = BeautifulSoup(response.content, "html.parser")

        # Check for various heading tags
        print("\n--- HEADING TAGS FOUND ---")
        for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            tags = soup.find_all(tag)
            if tags:
                print(f"\n{tag.upper()} tags ({len(tags)} found):")
                for i, t in enumerate(tags[:15]):  # Show first 15
                    text = t.get_text(strip=True)
                    if text:
                        print(f"  {i+1}. {text}")

        # Look for the expected section
        print(f"\n--- LOOKING FOR: '{section_title}' ---")
        section_header = None

        # Try different heading tags
        for heading_tag in ["h2", "h3", "h4"]:
            # Exact match
            section_header = soup.find(heading_tag, string=section_title)
            if section_header:
                print(f"✅ Found with {heading_tag} exact match")
                break

            # Case-insensitive match
            section_header = soup.find(heading_tag, string=lambda s: s and s.strip().lower() == section_title.lower())
            if section_header:
                print(f"✅ Found with {heading_tag} case-insensitive match: '{section_header.get_text(strip=True)}'")
                break

        if section_header:
            print(f"\n--- ANALYZING STRUCTURE AFTER HEADER ---")
            print(f"Header tag: {section_header.name}")
            print(f"Header text: {section_header.get_text(strip=True)}")

            # Look at siblings and children
            next_div = section_header.find_next("div")
            print(f"\nNext div exists: {next_div is not None}")
            if next_div:
                print(f"Next div classes: {next_div.get('class', [])}")

                # Look for table structures
                table = next_div.find("table")
                tbody = next_div.find("tbody")
                print(f"Contains table: {table is not None}")
                print(f"Contains tbody: {tbody is not None}")

                if tbody:
                    rows = tbody.find_all("tr")
                    print(f"Number of rows: {len(rows)}")

                    if rows:
                        print("\n--- FIRST ROW STRUCTURE ---")
                        first_row = rows[0]
                        tds = first_row.find_all("td")
                        print(f"Number of td elements: {len(tds)}")

                        for i, td in enumerate(tds[:5]):  # Show first 5 TDs
                            print(f"\nTD {i+1}:")
                            print(f"  Classes: {td.get('class', [])}")
                            print(f"  Text: {td.get_text(strip=True)[:50]}")
                            a_tag = td.find("a")
                            if a_tag:
                                print(f"  Contains link: {a_tag.get('href', 'no href')}")

        else:
            print("\n❌ Section header not found with any common method")
            print("\nListing all text content that might be section headers:")
            # Look for any element containing "Movies" or "Shows" or "TOP 10"
            keywords = ["Movies", "Shows", "TOP 10", "TV Shows"]
            for keyword in keywords:
                elements = soup.find_all(string=lambda text: text and keyword in text)
                if elements:
                    print(f"\nElements containing '{keyword}':")
                    for elem in list(elements)[:10]:
                        parent = elem.parent
                        print(f"  - Tag: {parent.name}, Text: {elem.strip()[:100]}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


def test_scraper(url, section_title):
    """Test the actual scraper with the URL."""
    print(f"\n{'='*80}")
    print(f"TESTING SCRAPER")
    print(f"URL: {url}")
    print(f"Section: {section_title}")
    print("=" * 80)

    result = scrape_top10(url, section_title)

    if result is None:
        print("❌ Scraper returned None - Check logs above for details")
    elif len(result) == 0:
        print("⚠️  Scraper returned empty list - Section might not be found")
    else:
        print(f"✅ Scraper found {len(result)} items:")
        for rank, title, slug in result:
            print(f"   {rank}. {title} ({slug})")


if __name__ == "__main__":
    print("=" * 80)
    print("FlixPatrol Diagnostic Tool")
    print("=" * 80)

    # Test Netflix Portugal page
    url = "https://flixpatrol.com/top10/netflix/portugal/"

    print("\n\n### Testing Movies Section ###")
    diagnose_page(url, "TOP 10 Movies")
    test_scraper(url, "TOP 10 Movies")

    print("\n\n### Testing TV Shows Section ###")
    diagnose_page(url, "TOP 10 TV Shows")
    test_scraper(url, "TOP 10 TV Shows")

    print("\n\n" + "=" * 80)
    print("Diagnostic complete!")
    print("=" * 80)
