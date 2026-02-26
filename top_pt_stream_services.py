import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ============================
# CONFIGURATION
# ============================
class Config:
    """Configuration management for the streaming services tracker."""

    def __init__(self):
        # Load environment variables
        self.CLIENT_ID = os.getenv("CLIENT_ID")
        self.ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
        self.KIDS_LIST = os.getenv("KIDS_LIST", "False").lower() in ("true", "True")
        self.PRINT_LISTS = os.getenv("PRINT_LISTS", "False").lower() in ("true", "True")
        self.TMDB_API_KEY = os.getenv("TMDB_API_KEY")

        # Request configuration
        self.REQUEST_TIMEOUT = 30  # seconds
        self.MAX_RETRIES = 10
        self.BACKOFF_FACTOR = 2

        # Dates
        self.yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # URLs
        self.urls = {
            "netflix": "https://flixpatrol.com/top10/netflix/portugal/",
            "netflix_kids": f"https://flixpatrol.com/top10/netflix/portugal/{self.yesterday_date}/",
            "hbo": "https://flixpatrol.com/top10/hbo-max/portugal/",
            "disney": "https://flixpatrol.com/top10/disney/portugal/",
            "apple": "https://flixpatrol.com/top10/apple-tv/portugal/",
            "prime": "https://flixpatrol.com/top10/amazon-prime/portugal/",
        }

        # Section names (used by all services: Netflix, HBO, Apple, Prime, Disney)
        self.sections = {
            "movies": "TOP 10 Movies",
            "shows": "TOP 10 TV Shows",
            "kids_movies": "TOP 10 Kids Movies",
            "kids_shows": "TOP 10 Kids TV Shows",
            "overall": "TOP 10 Overall",
        }


class TMDBRateLimiter:
    """Rate limiter for TMDB API to respect the 40 requests per 10 seconds limit."""

    def __init__(self, max_requests: int = 40, time_window: int = 10):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []

    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limits."""
        now = time.time()
        # Remove requests older than the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]

        if len(self.requests) >= self.max_requests:
            # Calculate how long to wait
            oldest_request = self.requests[0]
            wait_time = self.time_window - (now - oldest_request)
            if wait_time > 0:
                logging.debug("Rate limit reached, waiting %.2f seconds", wait_time)
                time.sleep(wait_time)
                # Clean up old requests after waiting
                now = time.time()
                self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]

        # Record this request
        self.requests.append(time.time())


# ============================
# GLOBAL VARIABLES (for backward compatibility)
# ============================
config = Config()
tmdb_rate_limiter = TMDBRateLimiter()


def _create_retry_session(
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple = (429, 500, 502, 503, 504),
) -> requests.Session:
    """Create a requests.Session with automatic retry and exponential backoff.

    Retries are applied to GET requests that fail with connection errors,
    timeouts, or the HTTP status codes in ``status_forcelist``.
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# Module-level retry-capable session for all HTTP requests (scraping)
_http_session = _create_retry_session()

# Dedicated TMDB session: carries the api_key as a default query parameter
# so it never appears in URL string literals or tracebacks.
_tmdb_session: Optional[requests.Session] = None


def _get_tmdb_session() -> requests.Session:
    """Return a retry-capable session pre-configured with the TMDB API key.

    The key is attached via ``session.params`` so it is automatically appended
    to every request made through this session without appearing in URL
    string literals (safer for tracebacks and logs).
    """
    global _tmdb_session
    if _tmdb_session is None:
        _tmdb_session = _create_retry_session()
        if config.TMDB_API_KEY:
            _tmdb_session.params = {"api_key": config.TMDB_API_KEY}  # type: ignore[assignment]
    return _tmdb_session


# Browser-like headers for FlixPatrol scraping (module-level constant)
SCRAPE_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Cookie": "_nss=1",
}
CLIENT_ID = config.CLIENT_ID
ACCESS_TOKEN = config.ACCESS_TOKEN
KIDS_LIST = config.KIDS_LIST
PRINT_LISTS = config.PRINT_LISTS
REQUEST_TIMEOUT = config.REQUEST_TIMEOUT
MAX_RETRIES = config.MAX_RETRIES
BACKOFF_FACTOR = config.BACKOFF_FACTOR

# Top kids only available on "yesterday" page so we need to get yesterday's date
yesterday_date = config.yesterday_date

# Flixpatrol URLs
top_netflix_url = config.urls["netflix"]
top_netflix_kids_url = config.urls["netflix_kids"]
top_hbo_url = config.urls["hbo"]
top_disney_url = config.urls["disney"]
top_apple_url = config.urls["apple"]
top_prime_url = config.urls["prime"]

# Sections Names
top_movies_section = config.sections["movies"]
top_shows_section = config.sections["shows"]
top_kids_movies_section = config.sections["kids_movies"]
top_kids_shows_section = config.sections["kids_shows"]
top_overrall_section = config.sections["overall"]

# Trakt Lists Data

# Netflix
trakt_netflix_movies_list_data = {
    "name": "Top Portugal Netflix Movies",
    "description": "List that contains the top 10 movies on Netflix Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}

trakt_netflix_shows_list_data = {
    "name": "Top Portugal Netflix Shows",
    "description": "List that contains the top 10 TV shows on Netflix Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}

trakt_netflix_kids_movies_list_data = {
    "name": "Top Portugal Netflix Kids Movies",
    "description": "List that contains the top 10 kids movies on Netflix Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}

trakt_netflix_kids_shows_list_data = {
    "name": "Top Portugal Netflix Kids Shows",
    "description": "List that contains the top 10 kids TV shows on Netflix Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}

# HBO
trakt_hbo_movies_list_data = {
    "name": "Top Portugal HBO Movies",
    "description": "List that contains the top 10 movies on HBO Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}

trakt_hbo_shows_list_data = {
    "name": "Top Portugal HBO Shows",
    "description": "List that contains the top 10 TV shows on HBO Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}

# Disney+
trakt_disney_top_list_data = {
    "name": "Top Portugal Disney+",
    "description": "List that contains the top movies and shows on Disney+ Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}

# Apple TV
trakt_apple_movies_list_data = {
    "name": "Top Portugal Apple TV Movies",
    "description": "List that contains the top 10 movies on Apple TV Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}

trakt_apple_shows_list_data = {
    "name": "Top Portugal Apple TV Shows",
    "description": "List that contains the top 10 TV shows on Apple TV Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}

# Amazon Prime
trakt_prime_movies_list_data = {
    "name": "Top Portugal Amazon Prime Movies",
    "description": "List that contains the top 10 movies on Amazon Prime Video Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}

trakt_prime_shows_list_data = {
    "name": "Top Portugal Amazon Prime Shows",
    "description": "List that contains the top 10 TV shows on Amazon Prime Video Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True,
}


# Trakt List slugs
trakt_netflix_movies_list_slug = "top-portugal-netflix-movies"
trakt_netflix_shows_list_slug = "top-portugal-netflix-shows"
trakt_netflix_kids_movies_list_slug = "top-portugal-netflix-kids-movies"
trakt_netflix_kids_shows_list_slug = "top-portugal-netflix-kids-shows"

trakt_hbo_movies_list_slug = "top-portugal-hbo-movies"
trakt_hbo_shows_list_slug = "top-portugal-hbo-shows"

trakt_disney_list_slug = "top-portugal-disney"

trakt_apple_movies_list_slug = "top-portugal-apple-tv-movies"
trakt_apple_shows_list_slug = "top-portugal-apple-tv-shows"

trakt_prime_movies_list_slug = "top-portugal-amazon-prime-movies"
trakt_prime_shows_list_slug = "top-portugal-amazon-prime-shows"

# ============================
# TMDB ENRICHMENT HELPERS
# ============================

# Maximum number of TMDB candidates to validate via the credits API
CREDITS_VALIDATION_LIMIT = 20


def _normalize_title(title: str) -> str:
    """Normalize a title for comparison: lowercase, strip leading articles, collapse whitespace."""
    normalized = title.lower().strip()
    # Strip common leading articles
    for article in ("the ", "a ", "an ", "o ", "os ", "as "):
        if normalized.startswith(article):
            normalized = normalized[len(article) :]
            break
    return normalized


def _extract_year_from_item(item: Dict[str, Any]) -> Optional[int]:
    """Extract the release year from a TMDB search result item.

    Movies use 'release_date', TV shows use 'first_air_date'. Both are formatted as 'YYYY-MM-DD'.
    """
    date_str = item.get("release_date") or item.get("first_air_date") or ""
    if date_str and len(date_str) >= 4:
        try:
            return int(date_str[:4])
        except ValueError:
            pass
    return None


def _extract_result_info(item: Dict[str, Any], media_type_override: Optional[str] = None) -> Dict[str, Any]:
    """Extract standard fields from a TMDB search result item.

    Args:
        item: A single TMDB search result dict.
        media_type_override: Override for media_type (used when calling type-specific endpoints
                              that don't return a media_type field).

    Returns:
        Dict with keys: tmdb_id, media_type, imdb_id (always None from search), year.
    """
    media_type = media_type_override or item.get("media_type", "movie")
    return {
        "tmdb_id": item.get("id"),
        "media_type": media_type,
        "imdb_id": None,
        "year": _extract_year_from_item(item),
    }


def _get_tmdb_title(item: Dict[str, Any]) -> str:
    """Get the display title from a TMDB result (movies use 'title', TV uses 'name')."""
    return item.get("title") or item.get("name") or ""


def _match_person_in_credits(
    credits_data: Dict[str, Any],
    person_name_lower: str,
) -> bool:
    """Check whether a person appears anywhere in TMDB credits (cast or crew).

    Searches the full cast list and the full crew list so the match succeeds
    regardless of the person's actual role (actor, director, producer, writer, etc.).

    Args:
        credits_data: The ``credits`` dict from a TMDB details response.
        person_name_lower: Lower-cased person name from FlixPatrol.

    Returns:
        True if a bidirectional substring match is found.
    """
    members = list(credits_data.get("cast", []))
    members.extend(credits_data.get("crew", []))

    for member in members:
        member_name = member.get("name", "").lower()
        if person_name_lower in member_name or member_name in person_name_lower:
            return True
    return False


def validate_by_credits(
    candidates: List[Dict[str, Any]],
    starring: str,
    content_hint: Optional[str],
    person_role: str = "cast",
) -> Optional[Dict[str, Any]]:
    """Validate TMDB candidates by checking if a FlixPatrol person appears in credits.

    Fetches TMDB details with credits and external_ids for up to CREDITS_VALIDATION_LIMIT candidates.
    Returns full enrichment data (tmdb_id, media_type, imdb_id) for the first match.

    Args:
        candidates: List of TMDB search result dicts to check.
        starring: Person name from FlixPatrol (actor, director, or producer).
        content_hint: "movie", "series", or None. Used to determine the TMDB endpoint.
        person_role: "cast", "director", or "producer" -- determines which TMDB credits
                     list to search (cast vs crew filtered by job).

    Returns:
        Enrichment dict if a credits match is found, None otherwise.
    """
    if not config.TMDB_API_KEY or not starring:
        return None

    starring_lower = starring.lower()

    for item in candidates[:CREDITS_VALIDATION_LIMIT]:
        tmdb_id = item.get("id")
        if not tmdb_id:
            continue

        # Determine endpoint: use media_type from search result if available, else content_hint
        item_media_type = item.get("media_type")
        if item_media_type == "movie":
            endpoint = "movie"
        elif item_media_type == "tv":
            endpoint = "tv"
        elif content_hint == "movie":
            endpoint = "movie"
        elif content_hint == "series":
            endpoint = "tv"
        else:
            # For Disney+ overall without media_type, try movie first
            endpoint = "movie"

        details_url = f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}" f"?append_to_response=credits,external_ids"

        try:
            tmdb_rate_limiter.wait_if_needed()
            response = _get_tmdb_session().get(details_url, timeout=config.REQUEST_TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                credits = data.get("credits", {})

                if _match_person_in_credits(credits, starring_lower):
                    logging.debug(
                        "Credits match: found '%s' (%s) in TMDB ID %s (%s)",
                        starring,
                        person_role,
                        tmdb_id,
                        _get_tmdb_title(item),
                    )
                    imdb_id = data.get("external_ids", {}).get("imdb_id")
                    media_type = item_media_type or ("movie" if endpoint == "movie" else "tv")
                    return {
                        "tmdb_id": tmdb_id,
                        "media_type": media_type,
                        "imdb_id": imdb_id,
                        "year": _extract_year_from_item(item) or _extract_year_from_item(data),
                    }
            elif response.status_code == 404 and endpoint == "movie" and content_hint is None:
                # For Disney+ overall: if movie endpoint 404s, retry as TV
                details_url_tv = (
                    f"https://api.themoviedb.org/3/tv/{tmdb_id}" f"?append_to_response=credits,external_ids"
                )
                tmdb_rate_limiter.wait_if_needed()
                response_tv = _get_tmdb_session().get(details_url_tv, timeout=config.REQUEST_TIMEOUT)
                if response_tv.status_code == 200:
                    data = response_tv.json()
                    credits = data.get("credits", {})

                    if _match_person_in_credits(credits, starring_lower):
                        logging.info(
                            "Credits match (TV retry): found '%s' (%s) in TMDB ID %s (%s)",
                            starring,
                            person_role,
                            tmdb_id,
                            _get_tmdb_title(item),
                        )
                        imdb_id = data.get("external_ids", {}).get("imdb_id")
                        return {
                            "tmdb_id": tmdb_id,
                            "media_type": "tv",
                            "imdb_id": imdb_id,
                            "year": _extract_year_from_item(item) or _extract_year_from_item(data),
                        }
            else:
                logging.debug("TMDB details fetch failed (status %s) for ID: %s", response.status_code, tmdb_id)

        except requests.exceptions.RequestException as error:
            logging.warning("TMDB credits request failed for ID %s: %s", tmdb_id, error)
        except Exception as error:
            logging.warning("Error checking credits for TMDB ID %s: %s", tmdb_id, error, exc_info=True)

    return None


# ============================
# HELPER METHODS
# ============================


# Get headers
def get_headers() -> Dict[str, str]:
    """Returns headers with authorization for requests."""
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "trakt-api-version": "2",
        "trakt-api-key": CLIENT_ID,
        "User-Agent": user_agent,
    }


# Print the results
def print_top_list(title: str, top_list: List[Tuple[str, str, str, str, str, str, str, str]]) -> None:
    if not top_list:
        logging.info("No data to display for %s", title)
        return

    logging.info("=" * 30)
    logging.info("%s", title)
    logging.info("=" * 30)
    for rank, item_title, title_tag, year, starring, tmdb_id, imdb_id, media_type in top_list:
        logging.info(
            "%s: %s | %s | %s | %s | %s | %s | %s",
            rank,
            item_title,
            title_tag,
            year,
            starring,
            tmdb_id,
            imdb_id,
            media_type,
        )


# ============================
# FLIXPATROL SCRAPING HELPERS
# ============================

# Ordered fallback chain for extracting a reference person from FlixPatrol.
# Each entry is (label_text, person_role).  ``person_role`` tells
# ``validate_by_credits`` whether to look in TMDB cast or crew.
_PERSON_LABELS: List[tuple] = [
    ("Starring", "cast"),
    ("Directed by", "director"),
    ("Produced by", "producer"),
]


def _extract_reference_person(soup: BeautifulSoup) -> tuple:
    """Extract a reference person from a FlixPatrol detail page.

    Tries the labels in ``_PERSON_LABELS`` order (Starring -> Directed by ->
    Produced by).  For each label, looks for a ``<dt>`` whose stripped,
    lower-cased text matches, then reads the first ``<a>`` inside the
    following ``<dd class="grow">`` sibling.

    Returns:
        (name, role) -- e.g. ("Adrien Brody", "cast") or ("Brady Corbet", "director").
        (None, "cast") if no person could be extracted.
    """
    for label_text, role in _PERSON_LABELS:
        label_lower = label_text.lower()
        dt_tag = soup.find("dt", string=lambda t: t is not None and t.strip().lower() == label_lower)
        if not dt_tag:
            continue
        dd_tag = dt_tag.find_next("dd", class_="grow")
        if not dd_tag:
            continue
        first_a = dd_tag.find("a")
        if first_a:
            name = first_a.get_text(strip=True)
            if name:
                logging.debug("Reference person: '%s' (role=%s, label='%s')", name, role, label_text)
                return (name, role)
    return (None, "cast")


def _content_hint_from_section(section_title: str) -> Optional[str]:
    """Derive a content_hint ("movie", "series", or None) from the FlixPatrol section title.

    "TOP 10 Movies" / "TOP 10 Kids Movies" -> "movie"
    "TOP 10 TV Shows" / "TOP 10 Kids TV Shows" -> "series"
    "TOP 10 Overall" -> None  (Disney+ mixed list)
    """
    lower = section_title.lower()
    if "movie" in lower:
        return "movie"
    if "tv show" in lower or "tv shows" in lower:
        return "series"
    return None


# Page cache: avoids re-fetching the same URL multiple times in a single run.
# Netflix's page contains all 4 sections (movies, shows, kids movies, kids shows)
# so we only need to fetch it once.
_page_cache: Dict[str, BeautifulSoup] = {}


# Scrape movie or show data based in the section title
def scrape_top10(url: str, section_title: str) -> Optional[List[Tuple[str, str, str, str, str, str, str, str]]]:
    """Scrape a top-10 section from a FlixPatrol page.

    Uses a per-run page cache so the same URL is fetched at most once
    (important for Netflix which has 4 sections on a single page).

    Returns:
        List of 8-tuples (rank, title, slug, year, starring, tmdb_id, imdb_id, media_type),
        or None if the request failed entirely.
    """
    data: List[Tuple[str, str, str, str, str, str, str, str]] = []
    content_hint = _content_hint_from_section(section_title)

    try:
        # Use cached page if available
        if url in _page_cache:
            soup = _page_cache[url]
            logging.debug("Using cached page for %s", url)
        else:
            response = _http_session.get(url, headers=SCRAPE_HEADERS, timeout=REQUEST_TIMEOUT)

            if response.status_code != 200:
                logging.error("Failed to retrieve page %s, status code: %s", url, response.status_code)
                return None

            soup = BeautifulSoup(response.content, "html.parser")
            _page_cache[url] = soup

        # Locate the correct section - search in document order, not heading tag order
        section_header = None
        all_headings = soup.find_all(["h2", "h3", "h4"])

        for heading in all_headings:
            heading_text = heading.get_text(strip=True)
            if heading_text == section_title:
                section_header = heading
                logging.debug("Found section '%s' with %s tag (exact match)", section_title, heading.name)
                break
            elif heading_text.lower() == section_title.lower():
                section_header = heading
                logging.debug("Found section '%s' with %s tag (case-insensitive)", section_title, heading.name)
                break

        if not section_header:
            logging.warning("Could not find section header for '%s' in %s", section_title, url)
            return data

        # Find parent card div (heading inside card)
        section_div = None
        parent = section_header.parent
        while parent and section_div is None:
            if parent.name == "div" and parent.get("class") and "card" in parent.get("class"):
                section_div = parent
                logging.debug("Found card div as parent of heading for %s", section_title)
                break
            parent = parent.parent
            if parent and parent.name == "body":
                break

        if not section_div:
            logging.warning("Could not find card div containing section header for %s", section_title)
            return data

        tbody = section_div.find("tbody")
        if not tbody:
            logging.warning("Could not find tbody in card div for %s", section_title)
            return data

        rows = tbody.find_all("tr")
        logging.debug("Found %d rows for %s", len(rows), section_title)

        for row in rows:
            try:
                # Extract rank: use first <td> (resilient against CSS changes)
                all_tds = row.find_all("td")
                rank_td = all_tds[0] if all_tds else None

                if not rank_td:
                    logging.warning("Could not find rank td in row for %s", section_title)
                    continue

                rank = rank_td.get_text(strip=True).rstrip(".")

                title_tag = row.find("a")
                if not title_tag:
                    logging.warning("Could not find title link in row for %s", section_title)
                    continue

                title = title_tag.get_text(strip=True)
                title_tag_href = title_tag.get("href", "")
                if not title_tag_href:
                    logging.warning("Title link has no href for %s: %s", section_title, title)
                    continue

                title_tag_slug = title_tag_href.split("/")[-2] if len(title_tag_href.split("/")) >= 2 else ""
                if not title_tag_slug:
                    logging.warning("Could not extract slug from href: %s", title_tag_href)
                    continue

                # Enrich with details from FlixPatrol detail page + TMDB
                year, starring, tmdb_id, imdb_id, media_type = scrape_details(
                    title_tag_slug, title, content_hint=content_hint
                )

                data.append((rank, title, title_tag_slug, year, starring, tmdb_id, imdb_id, media_type))
            except Exception as row_error:
                logging.warning("Error processing row in %s: %s", section_title, row_error)
                continue

        logging.info("Scraped %d items from %s", len(data), section_title)
        return data

    except requests.exceptions.RequestException as e:
        logging.error("Request failed for %s: %s", url, e)
        return None
    except Exception as e:
        logging.error("Error scraping %s: %s", url, e)
        return None


# Scrape the year, starring actor, TMDB id, and IMDb id for a title
def scrape_details(
    title_tag_slug: str, title: str, content_hint: Optional[str] = None
) -> Tuple[str, str, str, str, str]:
    """Scrape the detail page for a title and enrich with TMDB data.

    Args:
        title_tag_slug: FlixPatrol URL slug for the title.
        title: Display title of the entry.
        content_hint: "movie", "series", or None (Disney+ overall).
                      Used to pick the right TMDB search endpoint.

    Returns:
        Tuple of (year, starring, tmdb_id, imdb_id, media_type). All strings, "Unknown" if not found.
    """
    detail_url = f"https://flixpatrol.com/title/{title_tag_slug}"

    year = "Unknown"
    starring = "Unknown"
    tmdb_id = "Unknown"
    imdb_id = "Unknown"
    media_type = "Unknown"

    year_str: Optional[str] = None

    try:
        response = _http_session.get(detail_url, headers=SCRAPE_HEADERS, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract year
            premiere_div = soup.find("div", attrs={"title": "Premiere"})
            if premiere_div:
                span = premiere_div.find("span", class_="text-gray-600")
                span_text = span.get_text(strip=True) if span else ""
                year_text = ""
                if span and span.next_sibling:
                    sibling = span.next_sibling
                    if isinstance(sibling, NavigableString):
                        year_text = str(sibling).strip()
                    elif isinstance(sibling, Tag):
                        year_text = sibling.get_text(strip=True)
                if span_text and year_text:
                    year = f"{span_text} {year_text}"
                    year_str = year
                elif year_text:
                    year = year_text
                    year_str = year_text
                elif span_text:
                    # Only use span_text if it looks like a year (19xx or 20xx)
                    if re.search(r"\b(19|20)\d{2}\b", span_text):
                        year = span_text
                        year_str = span_text

            # Extract reference person for TMDB credits verification.
            # Tries Starring -> Directed by -> Produced by (first available).
            person_name, person_role = _extract_reference_person(soup)
            if person_name:
                starring = person_name

            # Extract media type from detail page as secondary signal (useful for Disney+ overall)
            # FlixPatrol detail pages contain "Movie" or "TV Show" in a metadata div
            detail_media_type = None
            type_div = soup.find("div", attrs={"title": "Type"})
            if type_div:
                type_text = type_div.get_text(strip=True).lower()
                if "movie" in type_text:
                    detail_media_type = "movie"
                elif "tv show" in type_text or "series" in type_text:
                    detail_media_type = "series"

            # For Disney+ overall (content_hint=None), use the detail page media type as hint
            effective_hint = content_hint
            if effective_hint is None and detail_media_type is not None:
                effective_hint = detail_media_type

            # TMDB enrichment -- pass content_hint, starring, and person_role for credits verification
            tmdb_id, media_type = search_tmdb(
                title,
                year_str or year,
                content_hint=effective_hint,
                starring=person_name,
                person_role=person_role,
            )
            if tmdb_id != "Unknown":
                imdb_id = get_tmdb_imdb_id(tmdb_id, media_type)
            else:
                logging.warning("TMDB ID not found for %s, skipping IMDb lookup", title)
        else:
            logging.warning("Failed to retrieve detail page %s (status %s)", detail_url, response.status_code)
    except requests.exceptions.RequestException as error:
        logging.warning("Request failed for detail page %s: %s", title_tag_slug, error)
    except Exception as error:
        logging.warning("Error scraping details for %s: %s", title_tag_slug, error)

    return year, starring, tmdb_id, imdb_id, media_type


def search_tmdb(
    title: str,
    year_str: str,
    content_hint: Optional[str] = None,
    starring: Optional[str] = None,
    person_role: str = "cast",
    _retried: bool = False,
) -> Tuple[str, str]:
    """Search TMDB for a title using a multi-step matching cascade.

    Matching cascade:
      1. Call the appropriate TMDB endpoint (type-specific when possible, no year in query).
         If no results and ``content_hint`` is type-specific, retry once with the
         opposite type (movie <-> series) before giving up.
      2. If only 1 result after filtering: use it (verify via credits).
      3. If multiple results and starring is available: disambiguate via credits API
         (up to CREDITS_VALIDATION_LIMIT candidates).
      4. If no credits match, try year-based match (local filtering only).
      5. If no year match, try exact title match (case-insensitive, normalized).
      6. Fallback: take the most popular result.

    Args:
        title: The title to search for.
        year_str: Year string from FlixPatrol (used for local filtering only, NOT sent to TMDB).
        content_hint: "movie", "series", or None (for Disney+ overall mixed lists).
        starring: Person name from FlixPatrol for credits-based validation.
        person_role: "cast", "director", or "producer" -- passed to ``validate_by_credits``.
        _retried: Internal guard to prevent infinite recursion on type-flip retry.

    Returns:
        Tuple of (tmdb_id_str, media_type_str). Both are "Unknown" if not found.
    """
    if not config.TMDB_API_KEY:
        return "Unknown", "Unknown"

    def _to_result(info: Dict[str, Any]) -> Tuple[str, str]:
        """Convert an enrichment dict to (tmdb_id_str, media_type) tuple."""
        tid = info.get("tmdb_id")
        mt = info.get("media_type", "movie")
        return (str(tid) if tid else "Unknown", mt if mt else "Unknown")

    def _verify_and_return(chosen_item: Dict[str, Any], step_label: str) -> Tuple[str, str]:
        """Verify a resolved candidate via credits when possible, then return."""
        if starring:
            verification = validate_by_credits([chosen_item], starring, content_hint, person_role)
            if verification:
                logging.debug(
                    "TMDB: %s for '%s' -- verified via %s credits",
                    step_label,
                    title,
                    person_role,
                )
                return _to_result(verification)
            else:
                logging.warning(
                    "TMDB: %s for '%s' -- could not verify via %s credits, using match anyway",
                    step_label,
                    title,
                    person_role,
                )
        return _to_result(_extract_result_info(chosen_item, media_type_override))

    # Step 1: Choose endpoint and search
    encoded_title = quote(title)

    if content_hint == "movie":
        search_url = f"https://api.themoviedb.org/3/search/movie?query={encoded_title}"
        media_type_override = "movie"
    elif content_hint == "series":
        search_url = f"https://api.themoviedb.org/3/search/tv?query={encoded_title}"
        media_type_override = "tv"
    else:
        # Disney+ overall or unknown: use multi-search
        search_url = f"https://api.themoviedb.org/3/search/multi?query={encoded_title}"
        media_type_override = None

    try:
        tmdb_rate_limiter.wait_if_needed()
        response = _get_tmdb_session().get(search_url, timeout=config.REQUEST_TIMEOUT)
        if response.status_code != 200:
            logging.warning("TMDB search failed (status %s) for: %s", response.status_code, title)
            return "Unknown", "Unknown"

        data = response.json()
        results = data.get("results", [])

        # Filter out "person" results when using /search/multi
        if media_type_override is None:
            results = [r for r in results if r.get("media_type") != "person"]

        if not results:
            if not _retried and content_hint in ("movie", "series"):
                alt_hint = "series" if content_hint == "movie" else "movie"
                logging.info(
                    "TMDB: no results for '%s' as %s, retrying as %s",
                    title,
                    content_hint,
                    alt_hint,
                )
                return search_tmdb(title, year_str, alt_hint, starring, person_role, _retried=True)
            logging.warning("TMDB search returned no results for: %s", title)
            return "Unknown", "Unknown"

        # Step 2: If only 1 result, use it directly (verify via credits)
        if len(results) == 1:
            return _verify_and_return(results[0], "single result")

        # Step 3: Credits-based disambiguation (when multiple results and starring available)
        if starring:
            logging.debug(
                "TMDB: checking credits for '%s' with '%s' (%s, %d candidates)",
                title,
                starring,
                person_role,
                len(results),
            )
            credits_match = validate_by_credits(results, starring, content_hint, person_role)
            if credits_match:
                return _to_result(credits_match)

        # Step 4: Try year-based local match (no re-verification -- credits already tried)
        year_match_re = re.search(r"\b(19|20)\d{2}\b", year_str) if year_str else None
        year_fragment = year_match_re.group(0) if year_match_re else ""

        if year_fragment:
            for item in results:
                release_date = item.get("release_date") or item.get("first_air_date")
                if release_date and release_date.startswith(year_fragment):
                    logging.debug(
                        "TMDB: year match (%s) for '%s' -> TMDB ID %s ('%s')",
                        year_fragment,
                        title,
                        item.get("id"),
                        _get_tmdb_title(item),
                    )
                    return _to_result(_extract_result_info(item, media_type_override))

        # Step 5: Try exact title match (no re-verification)
        normalized_search_title = _normalize_title(title)
        title_matches = []
        for item in results:
            tmdb_title = _get_tmdb_title(item)
            if _normalize_title(tmdb_title) == normalized_search_title:
                title_matches.append(item)

        if len(title_matches) == 1:
            logging.debug(
                "TMDB: single title match for '%s' -> TMDB ID %s ('%s')",
                title,
                title_matches[0].get("id"),
                _get_tmdb_title(title_matches[0]),
            )
            return _to_result(_extract_result_info(title_matches[0], media_type_override))

        # Step 6: Fallback -- take the most popular result (no re-verification)
        fallback = title_matches[0] if title_matches else results[0]
        logging.info(
            "TMDB: fallback to most popular result for '%s' -> TMDB ID %s ('%s')",
            title,
            fallback.get("id"),
            _get_tmdb_title(fallback),
        )
        return _to_result(_extract_result_info(fallback, media_type_override))

    except requests.exceptions.RequestException as error:
        logging.warning("TMDB search request failed for %s: %s", title, error)
    except (KeyError, ValueError) as error:
        logging.warning("Error parsing TMDB response for %s: %s", title, error)
    except Exception as error:
        logging.warning("Unexpected error searching TMDB for %s: %s", title, error, exc_info=True)

    return "Unknown", "Unknown"


def get_tmdb_imdb_id(tmdb_id: str, media_type: str) -> str:
    if not config.TMDB_API_KEY or tmdb_id == "Unknown":
        return "Unknown"

    endpoint = "movie" if media_type == "movie" else "tv"
    details_url = f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}" "?append_to_response=external_ids"

    try:
        tmdb_rate_limiter.wait_if_needed()
        response = _get_tmdb_session().get(details_url, timeout=config.REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            imdb_id = data.get("external_ids", {}).get("imdb_id")
            return imdb_id if imdb_id else "Unknown"
        logging.warning("TMDB details fetch failed (status %s) for ID: %s", response.status_code, tmdb_id)
    except requests.exceptions.RequestException as error:
        logging.warning("TMDB details request failed for %s: %s", tmdb_id, error)
    except (KeyError, ValueError) as error:
        logging.warning("Error parsing TMDB details for %s: %s", tmdb_id, error)
    except Exception as error:
        logging.warning("Unexpected error getting TMDB details for %s: %s", tmdb_id, error)

    return "Unknown"


def search_trakt_by_tmdb_id(tmdb_id: str, media_type: str) -> Optional[int]:
    """
    Search Trakt for a movie/show by TMDB ID.

    Args:
        tmdb_id: The TMDB ID to search for
        media_type: Either "movie" or "show"

    Returns:
        Trakt ID if found, None otherwise
    """
    if tmdb_id == "Unknown":
        return None

    response = requests.get(
        f"https://api.trakt.tv/search/tmdb/{tmdb_id}?type={media_type}",
        headers=get_headers(),
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code == 200:
        results = response.json()
        # Find the first result matching the requested type
        for result in results:
            if result["type"] == media_type:
                trakt_id = result[media_type]["ids"]["trakt"]
                logging.debug(f"Found Trakt ID {trakt_id} via TMDB ID {tmdb_id}")
                return trakt_id
        # No matching type found
        logging.debug(f"No {media_type} results for TMDB ID {tmdb_id}")
    else:
        logging.warning(f"Trakt TMDB search failed (status {response.status_code}) for ID: {tmdb_id}")

    return None


def search_trakt_by_tmdb_id_any_type(tmdb_id: str) -> Optional[Tuple[str, int]]:
    """
    Search Trakt by TMDB ID without type filter (for mixed lists).

    Args:
        tmdb_id: The TMDB ID to search for

    Returns:
        Tuple of (media_type, trakt_id) if found, None otherwise
    """
    if tmdb_id == "Unknown":
        return None

    response = requests.get(
        f"https://api.trakt.tv/search/tmdb/{tmdb_id}",
        headers=get_headers(),
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code == 200:
        results = response.json()
        # Filter to only movie/show results (TMDB IDs can also match people)
        for result in results:
            media_type = result["type"]
            if media_type in ("movie", "show"):
                trakt_id = result[media_type]["ids"]["trakt"]
                logging.debug(f"Found Trakt ID {trakt_id} ({media_type}) via TMDB ID {tmdb_id}")
                return media_type, trakt_id
        # No movie/show found
        logging.debug(f"No movie/show results for TMDB ID {tmdb_id} (may be a person)")
    else:
        logging.warning(f"Trakt TMDB search failed (status {response.status_code}) for ID: {tmdb_id}")

    return None


# parse items from trakt list
def parse_items(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    movies = []
    shows = []
    for item in items:
        if item["type"] == "movie":
            movie_data = {"ids": {"trakt": item["movie"]["ids"]["trakt"]}}
            movies.append(movie_data)
        elif item["type"] == "show":
            show_data = {"ids": {"trakt": item["show"]["ids"]["trakt"]}}
            shows.append(show_data)
    payload = {"movies": movies, "shows": shows}
    return payload


# Decorator to retry requests
def retry_request(func):
    def wrapper(*args, **kwargs):
        attempts = MAX_RETRIES
        for attempt in range(attempts):
            response = func(*args, **kwargs)
            if (
                response
                and response == 304
                or (hasattr(response, "status_code") and response.status_code in [200, 201])
            ):
                return response
            logging.warning(
                f"Attempt {attempt + 1} failed with {getattr(response, 'status_code', 'unknown status')}. Retrying..."
            )
            time.sleep(BACKOFF_FACTOR**attempt)
        logging.error("All attempts to update the list failed.")
        return None

    return wrapper


# ============================
# TRAKT METHODS
# ============================


# Check Trakt access token
def check_token() -> Union[bool, int]:
    response = requests.get("https://api.trakt.tv/users/me", headers=get_headers(), timeout=REQUEST_TIMEOUT)
    if response.status_code == 200:
        # TO DO - Implement a refresh token method when the access token is almost expired
        return True
    else:
        return response.status_code


# Get Trakt user's lists
def get_lists() -> List[Dict[str, Any]]:
    response = requests.get("https://api.trakt.tv/users/me/lists", headers=get_headers(), timeout=REQUEST_TIMEOUT)
    return response.json()


# Get a list by ID
def get_list(list_id: str) -> Dict[str, Any]:
    response = requests.get(
        f"https://api.trakt.tv/users/me/lists/{list_id}", headers=get_headers(), timeout=REQUEST_TIMEOUT
    )
    return response.json()


# Get list id by slug
def get_list_id(list_slug: str) -> Optional[int]:
    lists = get_lists()
    for list in lists:
        if list["ids"]["slug"] == list_slug:
            return list["ids"]["trakt"]
    return None


# Get a list items
def get_list_items(list_id: str) -> Dict[str, List[Dict[str, Any]]]:
    response = requests.get(
        f"https://api.trakt.tv/users/me/lists/{list_id}/items", headers=get_headers(), timeout=REQUEST_TIMEOUT
    )
    parsed_items = parse_items(response.json())
    return parsed_items


# Delete a list by ID
def delete_list(list_id: str) -> int:
    response = requests.delete(
        f"https://api.trakt.tv/users/me/lists/{list_id}", headers=get_headers(), timeout=REQUEST_TIMEOUT
    )
    return response.status_code


@retry_request
def create_list(list_data: Dict[str, Any]) -> requests.Response:
    response = requests.post(
        "https://api.trakt.tv/users/me/lists", headers=get_headers(), json=list_data, timeout=REQUEST_TIMEOUT
    )
    if response and response.status_code == 201:
        logging.info(f"List '{list_data['name']}' created successfully.")
    return response


# Empty a list
def empty_list(list_id: str) -> int:
    logging.info("Emptying list...")
    list_items = get_list_items(list_id)
    response = requests.post(
        f"https://api.trakt.tv/users/me/lists/{list_id}/items/remove",
        headers=get_headers(),
        json=list_items,
        timeout=REQUEST_TIMEOUT,
    )
    logging.info("List emptied")
    return response.status_code


# Check necessary lists
def check_lists() -> bool:
    lists = get_lists()
    lists_slugs = [list["ids"]["slug"] for list in lists]
    logging.debug(f"Lists slugs: {lists_slugs}")
    error_create = False

    if trakt_netflix_movies_list_slug not in lists_slugs:
        error_create = create_list(trakt_netflix_movies_list_data)
    if trakt_netflix_shows_list_slug not in lists_slugs:
        error_create = create_list(trakt_netflix_shows_list_data)
    if KIDS_LIST:
        if trakt_netflix_kids_movies_list_slug not in lists_slugs:
            error_create = create_list(trakt_netflix_kids_movies_list_data)
        if trakt_netflix_kids_shows_list_slug not in lists_slugs:
            error_create = create_list(trakt_netflix_kids_shows_list_data)
    if trakt_hbo_movies_list_slug not in lists_slugs:
        error_create = create_list(trakt_hbo_movies_list_data)
    if trakt_hbo_shows_list_slug not in lists_slugs:
        error_create = create_list(trakt_hbo_shows_list_data)
    if trakt_disney_list_slug not in lists_slugs:
        error_create = create_list(trakt_disney_top_list_data)
    if trakt_apple_movies_list_slug not in lists_slugs:
        error_create = create_list(trakt_apple_movies_list_data)
    if trakt_apple_shows_list_slug not in lists_slugs:
        error_create = create_list(trakt_apple_shows_list_data)
    if trakt_prime_movies_list_slug not in lists_slugs:
        error_create = create_list(trakt_prime_movies_list_data)
    if trakt_prime_shows_list_slug not in lists_slugs:
        error_create = create_list(trakt_prime_shows_list_data)
    logging.debug("Lists checked!")
    return bool(error_create)


# Search movies or shows by title and type
def search_title_by_type(title_info: Tuple[str, str], media_type: str) -> List[int]:
    title = title_info[0].replace("&", "and")
    title_tag = title_info[1]

    response = requests.get(
        f"https://api.trakt.tv/search/{media_type}?query={title}&extended=full",
        headers=get_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    trakt_ids = []
    if response.status_code == 200:
        results = response.json()
        logging.debug(f"Results: {results} for title: {title}")
        for result in results:
            logging.debug("Comparing " + title + " with: " + result[media_type]["title"].lower())
            normalized_slug = result[media_type]["ids"]["slug"].replace("-", "")
            normalized_title_tag = title_tag.replace("-", "")
            if (
                result["type"] == media_type
                and result[media_type]["title"].lower() == title.lower()
                and (normalized_title_tag in normalized_slug or normalized_title_tag.startswith(normalized_slug))
                or (
                    normalized_title_tag in normalized_slug
                    or normalized_title_tag.startswith(normalized_slug)
                    or normalized_slug.startswith(normalized_title_tag)
                )
            ):
                trakt_id = result[media_type]["ids"]["trakt"]
                trakt_ids.append(trakt_id)
                logging.debug(f"Added trakt id: {trakt_id} with slug {normalized_slug} for title: {title}")
                break
        if trakt_ids == [] and results:
            logging.warning(f"Title not found: {title}, will add first result : {results[0][media_type]['title']}")
            trakt_ids.append(results[0][media_type]["ids"]["trakt"])
        elif trakt_ids == [] and not results:
            logging.warning(f"No results found for title: {title}")
    else:
        logging.error(f"Error: {response.status_code}")
    return trakt_ids


# Search movies and shows by title
def search_title(title_info: Tuple[str, str, str]) -> List[Tuple[str, int, str]]:
    title = title_info[0].replace("&", "and")
    title_tag = title_info[1]
    rank = title_info[2]

    response = requests.get(
        f"https://api.trakt.tv/search/movie,show?query={title}&extended=full",
        headers=get_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    trakt_info = []
    if response.status_code == 200:
        results = response.json()
        logging.debug(f"Results: {results} for title: {title}")
        for result in results:
            media_type = result["type"]
            normalized_slug = result[media_type]["ids"]["slug"].replace("-", "")
            normalized_title_tag = title_tag.replace("-", "")
            logging.debug(
                "Comparing "
                + title
                + " and tag "
                + normalized_title_tag
                + " with: "
                + result[media_type]["title"].lower()
                + " and slug "
                + normalized_slug
            )
            if (
                result[media_type]["title"].lower() == title.lower()
                and (normalized_title_tag in normalized_slug or normalized_title_tag.startswith(normalized_slug))
                or (normalized_title_tag in normalized_slug or normalized_title_tag.startswith(normalized_slug))
            ):
                trakt_id = result[media_type]["ids"]["trakt"]
                trakt_info.append((media_type, trakt_id, rank))
                logging.debug(f"Added trakt id: {trakt_id} with slug {normalized_slug} for title: {title}")
                break
        if trakt_info == [] and results:
            media_type_0 = results[0]["type"]
            logging.warning(f"Title not found: {title}, will add first result : {results[0][media_type_0]['title']}")
            trakt_info.append((media_type_0, results[0][media_type_0]["ids"]["trakt"], rank))
        elif trakt_info == [] and not results:
            logging.warning(f"No results found for title: {title}")
    else:
        logging.error(f"Error: {response.status_code}")
    return trakt_info


# Create a Trakt list payload based on the top movies and shows list
def create_type_trakt_list_payload(
    top_list: List[Tuple[str, str, str, str, str, str, str, str]], media_type: str
) -> Dict[str, List[Dict[str, Any]]]:
    """Create a Trakt list payload based on the top movies or shows list.

    Uses TMDB ID search when available, falls back to title search otherwise.
    """
    trakt_ids = []

    for rank, title, title_tag, year, starring, tmdb_id, imdb_id, _media_type in top_list:
        trakt_id = None

        # Try TMDB ID search first
        if tmdb_id != "Unknown":
            trakt_id = search_trakt_by_tmdb_id(tmdb_id, media_type)

        # Fallback to title search
        if trakt_id is None:
            logging.debug(f"Falling back to title search for: {title}")
            title_results = search_title_by_type((title, title_tag), media_type)
            if title_results:
                trakt_id = title_results[0]

        if trakt_id:
            trakt_ids.append(trakt_id)

    # Create the payload
    payload: Dict[str, List[Dict[str, Any]]] = {f"{media_type}s": []}
    for trakt_id in trakt_ids:
        payload[f"{media_type}s"].append({"ids": {"trakt": trakt_id}})

    logging.debug(f"Payload: {payload}")
    return payload


# Create a mixed Trakt list payload based on an overall top movies and shows list
def create_mixed_trakt_list_payload(
    top_list: List[Tuple[str, str, str, str, str, str, str, str]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Create a mixed Trakt list payload based on an overall top movies and shows list.

    Uses TMDB ID + media_type for type-filtered Trakt search when available,
    falls back to untyped TMDB search, then title search.
    """
    # Map TMDB media_type values to Trakt type values
    _TMDB_TO_TRAKT_TYPE = {"movie": "movie", "tv": "show"}

    payload: Dict[str, List[Dict[str, Any]]] = {"movies": [], "shows": []}

    for rank, title, title_tag, year, starring, tmdb_id, imdb_id, media_type in top_list:
        trakt_info = None

        if tmdb_id != "Unknown":
            # Prefer type-filtered search when media_type is known (avoids TMDB ID collisions)
            trakt_type = _TMDB_TO_TRAKT_TYPE.get(media_type)
            if trakt_type:
                trakt_id = search_trakt_by_tmdb_id(tmdb_id, trakt_type)
                if trakt_id is not None:
                    trakt_info = (trakt_type, trakt_id)

            # Fallback to untyped search if media_type was unknown or typed search failed
            if trakt_info is None:
                trakt_info = search_trakt_by_tmdb_id_any_type(tmdb_id)

        # Fallback to title search
        if trakt_info is None:
            logging.debug(f"Falling back to title search for: {title}")
            title_results = search_title((title, title_tag, rank))
            if title_results:
                result_type, trakt_id, _ = title_results[0]
                trakt_info = (result_type, trakt_id)

        if trakt_info:
            resolved_type, trakt_id = trakt_info
            payload[f"{resolved_type}s"].append({"ids": {"trakt": trakt_id}})

    logging.debug(f"Payload: {payload}")
    return payload


# Update a trakt list
@retry_request
def update_list(list_slug: str, payload: Dict[str, List[Dict[str, Any]]]) -> Union[requests.Response, int]:
    # Empty the list only if payload is not empty
    if payload.get("movies") or payload.get("shows"):
        empty_list(list_slug)
        logging.info(f"Updating list {list_slug} ...")
        response = requests.post(
            f"https://api.trakt.tv/users/me/lists/{list_slug}/items",
            headers=get_headers(),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code in [200, 201]:
            logging.info("List updated successfully")
        return response
    else:
        logging.warning("Payload is empty. No items to add on list " + list_slug)
        return 304


# ============================
# STREAMING SERVICE TRACKER CLASS
# ============================


class StreamingServiceTracker:
    """Main class for tracking streaming service data and updating Trakt lists."""

    def __init__(self, config_instance: Optional[Config] = None):
        """Initialize the tracker with configuration."""
        self.config = config_instance or config

        # Initialize list data
        self._init_list_data()

        # Performance optimization: cache for repeated calls
        self._headers_cache = None
        self._failed_services = set()  # Track failed services to avoid retrying

    def _init_list_data(self) -> None:
        """Initialize Trakt list data configurations."""
        # Netflix lists
        self.netflix_movies_list_data = {
            "name": "Top Portugal Netflix Movies",
            "description": "List that contains the top 10 movies on Netflix Portugal right now, updated daily",
            "privacy": "public",
            "display_numbers": True,
        }

        self.netflix_shows_list_data = {
            "name": "Top Portugal Netflix Shows",
            "description": "List that contains the top 10 TV shows on Netflix Portugal right now, updated daily",
            "privacy": "public",
            "display_numbers": True,
        }

        # Additional list configurations would go here...
        # For now, keeping it minimal to not duplicate all the list data

    def get_headers_cached(self) -> Dict[str, str]:
        """Get headers with caching for performance."""
        if self._headers_cache is None:
            self._headers_cache = get_headers()
        return self._headers_cache

    def run(self) -> int:
        """Main execution method."""
        try:
            logging.info("Starting streaming service data update...")

            # Extract Movies and TV Shows
            scraped_data = self._scrape_all_services()

            if self.config.PRINT_LISTS:
                self._print_scraped_data(scraped_data)

            # Check Trakt token and lists
            if not self._validate_trakt_setup():
                return -1

            # Update all lists
            self._update_all_lists(scraped_data)

            # Report execution summary
            self._report_execution_summary(scraped_data)

            logging.info("Finished updating lists")
            return 0

        except Exception as e:
            logging.error(f"Error in main execution: {e}")
            return -1

    def _scrape_all_services(self) -> Dict[str, Any]:
        """Scrape data from all streaming services with improved error handling."""
        scraped_data = {}

        # Define scraping tasks
        scraping_tasks = [
            ("netflix_movies", self.config.urls["netflix"], self.config.sections["movies"]),
            ("netflix_shows", self.config.urls["netflix"], self.config.sections["shows"]),
            ("netflix_kids_movies", self.config.urls["netflix_kids"], self.config.sections["kids_movies"]),
            ("netflix_kids_shows", self.config.urls["netflix_kids"], self.config.sections["kids_shows"]),
            ("hbo_movies", self.config.urls["hbo"], self.config.sections["movies"]),
            ("hbo_shows", self.config.urls["hbo"], self.config.sections["shows"]),
            ("disney_overall", self.config.urls["disney"], self.config.sections["overall"]),
            ("apple_movies", self.config.urls["apple"], self.config.sections["movies"]),
            ("apple_shows", self.config.urls["apple"], self.config.sections["shows"]),
            ("prime_movies", self.config.urls["prime"], self.config.sections["movies"]),
            ("prime_shows", self.config.urls["prime"], self.config.sections["shows"]),
        ]

        # Execute scraping tasks with error handling
        for task_name, url, section in scraping_tasks:
            try:
                result = scrape_top10(url, section)
                scraped_data[task_name] = result or []  # Ensure we always have a list
                if result is None:
                    logging.warning(f"Failed to scrape {task_name}")
                    self._failed_services.add(task_name)
                else:
                    logging.debug(f"Successfully scraped {task_name}: {len(result)} items")
            except Exception as e:
                logging.error(f"Error scraping {task_name}: {e}")
                scraped_data[task_name] = []
                self._failed_services.add(task_name)

        return scraped_data

    def _print_scraped_data(self, data: Dict[str, Any]) -> None:
        """Print all scraped data for debugging."""
        print_top_list("TOP Netflix Movies", data["netflix_movies"])
        print_top_list("TOP Netflix Shows", data["netflix_shows"])
        print_top_list("TOP Netflix Kids Movies", data["netflix_kids_movies"])
        print_top_list("TOP Netflix Kids Shows", data["netflix_kids_shows"])
        print_top_list("TOP HBO Movies", data["hbo_movies"])
        print_top_list("TOP HBO Shows", data["hbo_shows"])
        print_top_list("TOP Disney Overall", data["disney_overall"])
        print_top_list("TOP Apple TV Movies", data["apple_movies"])
        print_top_list("TOP Apple TV Shows", data["apple_shows"])
        print_top_list("TOP Amazon Prime Video Movies", data["prime_movies"])
        print_top_list("TOP Amazon Prime Video Shows", data["prime_shows"])

    def _validate_trakt_setup(self) -> bool:
        """Validate Trakt token and create necessary lists."""
        # Check the Trakt access token
        token_status = check_token()
        logging.info(f"Trakt access token status: {token_status}")
        if token_status is not True:
            return False

        # Check necessary lists
        if check_lists() is True:
            logging.error("Failed to create necessary lists")
            return False

        return True

    def _update_all_lists(self, data: Dict[str, Any]) -> None:
        """Update all Trakt lists with scraped data."""
        # List of streaming services and corresponding data
        streaming_services = [
            (
                "netflix",
                data["netflix_movies"],
                data["netflix_shows"],
                trakt_netflix_movies_list_slug,
                trakt_netflix_shows_list_slug,
            ),
            ("hbo", data["hbo_movies"], data["hbo_shows"], trakt_hbo_movies_list_slug, trakt_hbo_shows_list_slug),
            (
                "apple",
                data["apple_movies"],
                data["apple_shows"],
                trakt_apple_movies_list_slug,
                trakt_apple_shows_list_slug,
            ),
            (
                "prime",
                data["prime_movies"],
                data["prime_shows"],
                trakt_prime_movies_list_slug,
                trakt_prime_shows_list_slug,
            ),
        ]

        # Create and update lists for each streaming service
        for service, movies, shows, movies_slug, shows_slug in streaming_services:
            movies_update = create_type_trakt_list_payload(movies, "movie")
            shows_update = create_type_trakt_list_payload(shows, "show")

            update_list(movies_slug, movies_update)
            update_list(shows_slug, shows_update)

        # Handle Disney+ list as Disney stopped showing top movies and shows separately
        disney_update = create_mixed_trakt_list_payload(data["disney_overall"])
        update_list(trakt_disney_list_slug, disney_update)

        # Handle kids' lists
        if self.config.KIDS_LIST:
            kids_streaming_services = [
                (
                    "netflix",
                    data["netflix_kids_movies"],
                    data["netflix_kids_shows"],
                    trakt_netflix_kids_movies_list_slug,
                    trakt_netflix_kids_shows_list_slug,
                )
            ]

            for service, movies, shows, movies_slug, shows_slug in kids_streaming_services:
                movies_update = create_type_trakt_list_payload(movies, "movie")
                shows_update = create_type_trakt_list_payload(shows, "show")

                update_list(movies_slug, movies_update)
                update_list(shows_slug, shows_update)

    def _report_execution_summary(self, data: Dict[str, Any]) -> None:
        """Report summary of execution including successes and failures."""
        total_services = len(data)
        successful_services = sum(1 for v in data.values() if v and len(v) > 0)
        failed_services = len(self._failed_services)

        logging.info("Execution Summary:")
        logging.info(f"  Total services: {total_services}")
        logging.info(f"  Successful: {successful_services}")
        logging.info(f"  Failed: {failed_services}")

        if self._failed_services:
            logging.warning(f"  Failed services: {', '.join(self._failed_services)}")

        success_rate = (successful_services / total_services) * 100 if total_services > 0 else 0
        logging.info(f"  Success rate: {success_rate:.1f}%")


# ============================
# MAIN METHOD (backward compatibility)
# ============================


def main() -> int:
    """Main function for backward compatibility. Uses the StreamingServiceTracker class."""
    tracker = StreamingServiceTracker()
    return tracker.run()


if __name__ == "__main__":
    import sys

    sys.exit(main())
