import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

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
            "hbo": "https://flixpatrol.com/top10/hbo/portugal/",
            "disney": "https://flixpatrol.com/top10/disney/portugal/",
            "apple": "https://flixpatrol.com/top10/apple-tv/portugal/",
            "prime": "https://flixpatrol.com/top10/amazon-prime/portugal/",
        }

        # Section names
        self.sections = {
            "movies": "TOP 10 Movies",
            "shows": "TOP 10 TV Shows",
            "kids_movies": "TOP 10 Kids Movies",
            "kids_shows": "TOP 10 Kids TV Shows",
            "overall": "TOP 10 Overall",
        }


# ============================
# GLOBAL VARIABLES (for backward compatibility)
# ============================
config = Config()
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
def print_top_list(title: str, top_list: List[Tuple[str, str, str]]) -> None:
    logging.info("=" * 30)
    logging.info(f"{title}")
    logging.info("=" * 30)
    for rank, item_title, title_tag in top_list:
        logging.info(f"{rank}: {item_title} | {title_tag}")


# Scrape movie or show data based in the section title
def scrape_top10(url: str, section_title: str) -> Optional[List[Tuple[str, str, str]]]:
    data = []

    # Define headers to mimic a real browser
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
    headers = {
        "Content-Type": "application/json",
        "User-Agent": user_agent,
        "Cookie": "_nss=1",
    }

    try:
        # Send the GET request
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

        # Check for a successful response
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Locate the correct section - try multiple heading tags for robustness
            section_header = None
            for heading_tag in ["h2", "h3", "h4"]:
                # Try exact match first
                section_header = soup.find(heading_tag, string=section_title)
                if section_header:
                    logging.debug(f"Found section '{section_title}' with {heading_tag} tag")
                    break
                # Try case-insensitive match
                section_header = soup.find(
                    heading_tag, string=lambda s: s and s.strip().lower() == section_title.lower()
                )
                if section_header:
                    logging.debug(f"Found section '{section_title}' with {heading_tag} tag (case-insensitive)")
                    break

            # Check if the section was found
            if section_header:
                # Find the next div after the section header
                section_div = section_header.find_next("div", class_="card")
                if not section_div:
                    logging.warning(f"Could not find card div after section header for {section_title}")
                    return data

                tbody = section_div.find("tbody")  # Locate the table body within the div
                if not tbody:
                    logging.warning(f"Could not find tbody in card div for {section_title}")
                    return data

                rows = tbody.find_all("tr")
                logging.debug(f"Found {len(rows)} rows for {section_title}")

                for row in rows:
                    try:
                        # Try to find rank with specific class, fall back to first td if not found
                        rank_td = row.find(
                            "td",
                            class_="table-td w-12 font-semibold text-right text-gray-500 table-hover:text-gray-400",
                        )
                        if not rank_td:
                            # Fallback: try to find first td element
                            rank_td = row.find("td")

                        if not rank_td:
                            logging.warning(f"Could not find rank td in row for {section_title}")
                            continue

                        rank = rank_td.get_text(strip=True)

                        # Get the anchor tag containing the title
                        title_tag = row.find("a")
                        if not title_tag:
                            logging.warning(f"Could not find title link in row for {section_title}")
                            continue

                        title = title_tag.get_text(strip=True)  # Get the movie/show title
                        title_tag_href = title_tag.get("href", "")
                        if not title_tag_href:
                            logging.warning(f"Title link has no href for {section_title}: {title}")
                            continue

                        # Extract the title tag from the href
                        title_tag_slug = title_tag_href.split("/")[-2] if len(title_tag_href.split("/")) >= 2 else ""
                        if not title_tag_slug:
                            logging.warning(f"Could not extract slug from href: {title_tag_href}")
                            continue

                        rank = rank.rstrip(".")
                        data.append(
                            (rank, title, title_tag_slug)
                        )  # Append the rank, title, and title tag to the data list
                    except Exception as row_error:
                        logging.warning(f"Error processing row in {section_title}: {row_error}")
                        continue

                logging.info(f"Scraped {len(data)} items from {section_title}")
            else:
                logging.warning(f"Could not find section header for '{section_title}' in {url}")
            return data
        else:
            logging.error(f"Failed to retrieve page {url}, status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
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
    return error_create


# Search movies or shows by title and type
def search_title_by_type(title_info: Tuple[str, str], type: str) -> List[int]:
    title = title_info[0].replace("&", "and")
    title_tag = title_info[1]

    response = requests.get(
        f"https://api.trakt.tv/search/{type}?query={title}&extended=full",
        headers=get_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    trakt_ids = []
    if response.status_code == 200:
        results = response.json()
        logging.debug(f"Results: {results} for title: {title}")
        for result in results:
            logging.debug("Comparing " + title + " with: " + result[type]["title"].lower())
            normalized_slug = result[type]["ids"]["slug"].replace("-", "")
            normalized_title_tag = title_tag.replace("-", "")
            if (
                result["type"] == type
                and result[type]["title"].lower() == title.lower()
                and (normalized_title_tag in normalized_slug or normalized_title_tag.startswith(normalized_slug))
                or (
                    normalized_title_tag in normalized_slug
                    or normalized_title_tag.startswith(normalized_slug)
                    or normalized_slug.startswith(normalized_title_tag)
                )
            ):
                trakt_ids.append(result[type]["ids"]["trakt"])
                logging.debug(
                    f"Added trakt id: {result[type]['ids']['trakt']} with slug {normalized_slug} for title: {title}"
                )
                break
        if trakt_ids == []:
            logging.warning(f"Title not found: {title}, will add first result : {results[0][type]['title']}")
            trakt_ids.append(results[0][type]["ids"]["trakt"])
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
            type = result["type"]
            normalized_slug = result[type]["ids"]["slug"].replace("-", "")
            normalized_title_tag = title_tag.replace("-", "")
            logging.debug(
                "Comparing "
                + title
                + " and tag "
                + normalized_title_tag
                + " with: "
                + result[type]["title"].lower()
                + " and slug "
                + normalized_slug
            )
            if (
                result[type]["title"].lower() == title.lower()
                and (normalized_title_tag in normalized_slug or normalized_title_tag.startswith(normalized_slug))
                or (normalized_title_tag in normalized_slug or normalized_title_tag.startswith(normalized_slug))
            ):
                trakt_info.append((type, result[type]["ids"]["trakt"], rank))
                logging.debug(
                    f"Added trakt id: {result[type]['ids']['trakt']} with slug {normalized_slug} for title: {title}"
                )
                break
        if trakt_info == []:
            type_0 = results[0]["type"]
            logging.warning(f"Title not found: {title}, will add first result : {results[0][type_0]['title']}")
            trakt_info.append((type_0, results[0][type_0]["ids"]["trakt"], rank))
    else:
        logging.error(f"Error: {response.status_code}")
    return trakt_info


# Create a Trakt list payload based on the top movies and shows list
def create_type_trakt_list_payload(top_list: List[Tuple[str, str, str]], type: str) -> Dict[str, List[Dict[str, Any]]]:
    # get titles from top_list
    titles_info = [(title, title_tag) for _, title, title_tag in top_list]

    # get trakt ids from titles
    trakt_ids = []
    for title_info in titles_info:
        trakt_id = search_title_by_type(title_info, type)
        if trakt_id:
            trakt_ids.append(trakt_id[0])

    # create the payload
    payload = {f"{type}s": []}
    for trakt_id in trakt_ids:
        payload[f"{type}s"].append({"ids": {"trakt": trakt_id}})

    logging.debug(f"Payload: {payload}")
    return payload


# Create a mixed Trakt list payload based on an overral top movies and shows list
def create_mixed_trakt_list_payload(top_list: List[Tuple[str, str, str]]) -> Dict[str, List[Dict[str, Any]]]:
    # get titles from top_list
    titles_info = [(title, title_tag, rank) for rank, title, title_tag in top_list]

    # get trakt ids from titles
    trakt_infos = []
    for title_info in titles_info:
        trakt_info = search_title(title_info)
        logging.debug(f"Trakt info: {trakt_info}")
        if trakt_info:
            trakt_infos.append(trakt_info[0])

    # create the payload
    payload = {"movies": [], "shows": []}
    for type, trakt_id, rank in trakt_infos:
        payload[f"{type}s"].append({"ids": {"trakt": trakt_id}})

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

    def __init__(self, config_instance: Config = None):
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
