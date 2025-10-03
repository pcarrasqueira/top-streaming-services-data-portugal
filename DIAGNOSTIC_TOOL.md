# FlixPatrol Diagnostic Tool

This diagnostic script helps identify HTML structure changes on FlixPatrol's website and verify that the scraper can handle them correctly.

## Usage

```bash
python diagnose_flixpatrol.py
```

## What It Does

1. **Analyzes HTML Structure**: Examines the FlixPatrol page to identify:
   - What heading tags are used (h1, h2, h3, h4, etc.)
   - Where section titles are located
   - The structure of the card/table elements
   - TD classes and link structures

2. **Tests the Scraper**: Runs the actual `scrape_top10()` function to verify it can correctly extract data from the page.

3. **Provides Detailed Logging**: Shows debug information about what was found or what failed during the scraping process.

## Output

The script will output:
- ✅ Success indicators when the scraper works correctly
- ⚠️ Warnings when sections are not found
- ❌ Errors with detailed information about what went wrong
- Detailed HTML structure information for troubleshooting

## When to Use

Run this script when:
- The scraper stops working after FlixPatrol updates their website
- You want to verify the scraper works with the current FlixPatrol structure
- You need to debug scraping issues
- You want to understand what HTML changes FlixPatrol made

## Example Output

```
================================================================================
Diagnosing: https://flixpatrol.com/top10/netflix/portugal/
Expected section: TOP 10 Movies
================================================================================

Status code: 200

--- HEADING TAGS FOUND ---

H3 tags (5 found):
  1. TOP 10 Movies
  2. TOP 10 TV Shows
  3. Trending Now
  ...

--- LOOKING FOR: 'TOP 10 Movies' ---
✅ Found with h3 exact match

--- ANALYZING STRUCTURE AFTER HEADER ---
Header tag: h3
Header text: TOP 10 Movies
Next div exists: True
Next div classes: ['card']
Contains table: False
Contains tbody: True
Number of rows: 10

================================================================================
TESTING SCRAPER
================================================================================
✅ Scraper found 10 items:
   1. Movie Title 1 (movie-slug-1)
   2. Movie Title 2 (movie-slug-2)
   ...
```
