import logging
import time
import requests
import os

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ============================
# GLOBAL VARIABLES
# ============================
CLIENT_ID = os.getenv('CLIENT_ID')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
# Set to True if you want to include kids lists (Trakt limits to 10 lists per user)
# TO DO - use a different account to create the kids lists ?
KIDS_LIST = False

PRINT_LISTS = False

# Top kids only available on "yesterday" page so we need to get yesterday's date
yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# Flixpatrol URLs
top_netflix_url = "https://flixpatrol.com/top10/netflix/portugal/"
top_netflix_kids_url = f"https://flixpatrol.com/top10/netflix/portugal/{yesterday_date}/"
top_hbo_url = "https://flixpatrol.com/top10/hbo/portugal/"
top_disney_url = "https://flixpatrol.com/top10/disney/portugal/"
top_apple_url = "https://flixpatrol.com/top10/apple-tv/portugal/"
top_prime_url = "https://flixpatrol.com/top10/amazon-prime/portugal/"

# Sections Names
top_movies_section = "TOP 10 Movies"
top_shows_section = "TOP 10 TV Shows"
top_kids_movies_section = "TOP 10 Kids Movies"
top_kids_shows_section = "TOP 10 Kids TV Shows"
top_overrall_section = "TOP 10 Overall"

# Trakt Lists Data

# Netflix
trakt_netflix_movies_list_data = {
    "name": "Top Portugal Netflix Movies",
    "description": "List that contains the top 10 movies on Netflix Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
}

trakt_netflix_shows_list_data = {
    "name": "Top Portugal Netflix Shows",
    "description": "List that contains the top 10 TV shows on Netflix Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
}

trakt_netflix_kids_movies_list_data = {
    "name": "Top Portugal Netflix Kids Movies",
    "description": "List that contains the top 10 kids movies on Netflix Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
}

trakt_netflix_kids_shows_list_data = {
    "name": "Top Portugal Netflix Kids Shows",
    "description": "List that contains the top 10 kids TV shows on Netflix Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
}

# HBO
trakt_hbo_movies_list_data = {
    "name": "Top Portugal HBO Movies",
    "description": "List that contains the top 10 movies on HBO Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
}

trakt_hbo_shows_list_data = {
    "name": "Top Portugal HBO Shows",
    "description": "List that contains the top 10 TV shows on HBO Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
}

# Disney+
trakt_disney_top_list_data = {
    "name": "Top Portugal Disney+",
    "description": "List that contains the top movies and shows on Disney+ Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
}

# Apple TV
trakt_apple_movies_list_data = {
    "name": "Top Portugal Apple TV Movies",
    "description": "List that contains the top 10 movies on Apple TV Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
}

trakt_apple_shows_list_data = {
    "name": "Top Portugal Apple TV Shows",
    "description": "List that contains the top 10 TV shows on Apple TV Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
}

# Amazon Prime
trakt_prime_movies_list_data = {
    "name": "Top Portugal Amazon Prime Movies",
    "description": "List that contains the top 10 movies on Amazon Prime Video Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
}

trakt_prime_shows_list_data = {
    "name": "Top Portugal Amazon Prime Shows",
    "description": "List that contains the top 10 TV shows on Amazon Prime Video Portugal right now, updated daily",
    "privacy": "public",
    "display_numbers": True
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
def get_headers():
    """Returns headers with authorization for requests."""
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'trakt-api-version': '2',
        'trakt-api-key': CLIENT_ID
    }

# Print the results
def print_top_list(title, top_list):
    logging.info("="*30)
    logging.info(f"{title}")
    logging.info("="*30)
    for rank, item_title, title_tag in top_list:
        logging.info(f"{rank}: {item_title} | {title_tag}")

# Scrape movie or show data based in the section title
def scrape_top10(url, section_title):
    data = []

    # Define headers to mimic a real browser
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Cookie": "_nss=1"
    }

    # Send the GET request
    response = requests.get(url, headers=headers)

    # Check for a successful response
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Locate the correct section using 'h3' and the title
        section_header = soup.find("h3", string=section_title)
        # Check if the section was found
        if section_header:
            # Find the next div after the section header
            section_div = section_header.find_next("div", class_="card")
            tbody = section_div.find("tbody")  # Locate the table body within the div
            rows = tbody.find_all("tr")
            
            for row in rows:
                rank = row.find("td", class_="table-td w-12 font-semibold text-right text-gray-500 table-hover:text-gray-400").get_text(strip=True)  # Get the rank
                title_tag = row.find("a")  # Get the anchor tag containing the title
                title = title_tag.get_text(strip=True)  # Get the movie/show title
                title_tag_href = title_tag['href'].split('/')[-2]  # Extract the title tag from the href
                rank = rank.rstrip('.')
                data.append((rank, title, title_tag_href))  # Append the rank, title, and title tag to the data list
            logging.debug(f"Scraped {section_title} successfully")
        return data
    else:
        print(f"Failed to retrieve page, status code: {response.status_code}")
        return None

# parse items from trakt list
def parse_items(items):
    movies = []
    shows = []
    for item in items:
        if item['type'] == 'movie':
            movie_data = {
                "ids": {
                    "trakt": item['movie']['ids']['trakt']
                }
            }
            movies.append(movie_data)
        elif item['type'] == 'show':
            show_data = {
                "ids": {
                    "trakt": item['show']['ids']['trakt']
                }
            }
            shows.append(show_data)
    payload = {"movies": movies, "shows": shows}
    return payload

# Decorator to retry requests
def retry_request(func):
    def wrapper(*args, **kwargs):
        attempts = 10
        for attempt in range(attempts):
            response = func(*args, **kwargs)
            if response and response.status_code in [200, 201] or response == 304:
                return response
            logging.warning(f"Attempt {attempt + 1} failed with {response.status_code}. Retrying...")
            time.sleep(2 ** attempt)
        logging.error("All attempts to update the list failed.")
        return None
    return wrapper

# ============================
# TRAKT METHODS
# ============================

# Check Trakt access token
def check_token():
    response = requests.get('https://api.trakt.tv/users/me',headers=get_headers())
    if response.status_code == 200:
        # TO DO - Implement a refresh token method when the access token is almost expired
        return True
    else:
        return response.status_code

# Get Trakt user's lists
def get_lists():
    response = requests.get('https://api.trakt.tv/users/me/lists',headers=get_headers())
    return response.json()

# Get a list by ID
def get_list(list_id):
    response = requests.get(f'https://api.trakt.tv/users/me/lists/{list_id}',headers=get_headers())
    return response.json()

# Get list id by slug
def get_list_id(list_slug):
    lists = get_lists()
    for list in lists:
        if list['ids']['slug'] == list_slug:
            return list['ids']['trakt']
    return None

# Get a list items
def get_list_items(list_id):
    response = requests.get(f'https://api.trakt.tv/users/me/lists/{list_id}/items',headers=get_headers())
    parsed_items = parse_items(response.json())
    return parsed_items

# Delete a list by ID
def delete_list(list_id):
    response = requests.delete(f'https://api.trakt.tv/users/me/lists/{list_id}',headers=get_headers())
    return response.status_code

@retry_request
def create_list(list_data):
    response = requests.post('https://api.trakt.tv/users/me/lists', headers=get_headers(), json=list_data)
    if response and response.status_code == 201:
        logging.info(f"List '{list_data['name']}' created successfully.")
    return response

# Empty a list
def empty_list(list_id):
    logging.info("Emptying list...")
    list_items = get_list_items(list_id)
    response = requests.post(f'https://api.trakt.tv/users/me/lists/{list_id}/items/remove',headers=get_headers(),json=list_items)
    logging.info("List emptied")
    return response.status_code

# Check necessary lists
def check_lists():
    lists = get_lists()
    lists_slugs = [list['ids']['slug'] for list in lists]
    logging.debug(f"Lists slugs: {lists_slugs}")
    error_create = False

    if trakt_netflix_movies_list_slug not in lists_slugs:
        error_create = create_list( trakt_netflix_movies_list_data)
    if trakt_netflix_shows_list_slug not in lists_slugs:
        error_create = create_list( trakt_netflix_shows_list_data)
    if KIDS_LIST:
        if trakt_netflix_kids_movies_list_slug not in lists_slugs:
            error_create = create_list( trakt_netflix_kids_movies_list_data)
        if trakt_netflix_kids_shows_list_slug not in lists_slugs:
            error_create = create_list( trakt_netflix_kids_shows_list_data)
    if trakt_hbo_movies_list_slug not in lists_slugs:
        error_create = create_list( trakt_hbo_movies_list_data)
    if trakt_hbo_shows_list_slug not in lists_slugs:
        error_create = create_list( trakt_hbo_shows_list_data)
    if trakt_disney_list_slug not in lists_slugs:
        error_create = create_list( trakt_disney_top_list_data)
    if trakt_apple_movies_list_slug not in lists_slugs:
        error_create = create_list( trakt_apple_movies_list_data)
    if trakt_apple_shows_list_slug not in lists_slugs:
        error_create = create_list( trakt_apple_shows_list_data)
    if trakt_prime_movies_list_slug not in lists_slugs:
        error_create = create_list( trakt_prime_movies_list_data)
    if trakt_prime_shows_list_slug not in lists_slugs:
        error_create = create_list( trakt_prime_shows_list_data)
    logging.debug(f"Lists checked!")
    return error_create

# Search movies or shows by title and type
def search_title_by_type(title_info, type):
    title = title_info[0].replace('&', 'and')
    title_tag = title_info[1]

    response = requests.get(f'https://api.trakt.tv/search/{type}?query={title}&extended=full',headers=get_headers())
    trakt_ids = []
    if response.status_code == 200:
        results = response.json()
        logging.debug(f"Results: {results} for title: {title}")
        for result in results:
            logging.debug("Comparing " + title  + " with: " + result[type]['title'].lower())
            normalized_slug = result[type]['ids']['slug'].replace('-', '')
            normalized_title_tag = title_tag.replace('-', '')
            if result['type'] == type and result[type]['title'].lower() == title.lower() and (normalized_title_tag in normalized_slug or normalized_title_tag.startswith(normalized_slug)) or \
            (normalized_title_tag in normalized_slug or normalized_title_tag.startswith(normalized_slug) or normalized_slug.startswith(normalized_title_tag)):
                trakt_ids.append(result[type]['ids']['trakt'])
                logging.debug(f"Added trakt id: {result[type]['ids']['trakt']} with slug {normalized_slug} for title: {title}")
                break
        if trakt_ids == []:
            logging.warning(f"Title not found: {title}, will add first result : {results[0][type]['title']}")
            trakt_ids.append(results[0][type]['ids']['trakt'])
    else:
        logging.error(f"Error: {response.status_code}")
    return trakt_ids
               
# Search movies and shows by title
def search_title(title_info):
    title = title_info[0].replace('&', 'and')
    title_tag = title_info[1]

    response = requests.get(f'https://api.trakt.tv/search/movie,show?query={title}$&extended=full',headers=get_headers())
    trakt_info = []
    if response.status_code == 200:
        results = response.json()
        for result in results:
            type = result['type']
            normalized_slug = result[type]['ids']['slug'].replace('-', '')
            normalized_title_tag = title_tag.replace('-', '')
            logging.debug("Comparing " + title  + " with: " + result[type]['title'].lower())
            if result[type]['title'].lower() == title.lower() and (normalized_title_tag in normalized_slug or normalized_title_tag.startswith(normalized_slug)) or \
            (normalized_title_tag in normalized_slug or normalized_title_tag.startswith(normalized_slug) or normalized_slug.startswith(normalized_title_tag)):
                trakt_info.append((type, result[type]['ids']['trakt']))
                logging.debug(f"Added trakt id: {result[type]['ids']['trakt']} with slug {normalized_slug} for title: {title}")
                break
        if trakt_info == []:
            type_0 = results[0]['type']
            logging.warning(f"Title not found: {title}, will add first result : {results[0][type_0]['title']}")
            trakt_info.append((type_0, results[0][type_0]['ids']['trakt']))
    else:
        logging.error(f"Error: {response.status_code}")
    return trakt_info
  

# Create a Trakt list payload based on the top movies and shows list
def create_type_trakt_list_payload(top_list, type):
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
def create_mixed_trakt_list_payload(top_list):
    # get titles from top_list
    titles_info = [(title, title_tag) for _, title, title_tag in top_list]

    # get trakt ids from titles
    trakt_infos = []
    for title_info in titles_info:
        trakt_info = search_title(title_info)
        if trakt_info:
            trakt_infos.append(trakt_info[0])
    
    # create the payload
    payload = {"movies": [], "shows": []}
    for type, trakt_id in trakt_infos:
        payload[f"{type}s"].append({"ids": {"trakt": trakt_id}})
    
    logging.debug(f"Payload: {payload}")
    return payload
 
# Update a trakt list
@retry_request
def update_list(list, payload):
    # Empty the list only if payload is not empty
    if payload.get("movies") or payload.get("shows"):
        empty_list(list)
        logging.info(f"Updating list {list} ...")
        response = requests.post(f'https://api.trakt.tv/users/me/lists/{list}/items', headers=get_headers(), json=payload)
        if response.status_code in [200, 201]:
            logging.info(f"List updated successfully")
        return response
    else:
        logging.info("Payload is empty. No items to add on list " + list)
        return 304

# ============================
# MAIN METHOD
# ============================

def main():
    # Extract Movies and TV Shows

    # Netflix
    top_netflix_movies = scrape_top10(top_netflix_url, top_movies_section)
    top_netflix_shows = scrape_top10(top_netflix_url, top_shows_section)
    top_netflix_kids_movies = scrape_top10(top_netflix_kids_url, top_kids_movies_section)
    top_netflix_kids_shows = scrape_top10(top_netflix_kids_url, top_kids_shows_section)

    # HBO
    top_hbo_movies = scrape_top10(top_hbo_url, top_movies_section)
    top_hbo_shows = scrape_top10(top_hbo_url, top_shows_section)

    # Disney+
    top_overrall = scrape_top10(top_disney_url, top_overrall_section)

    # Apple TV
    top_apple_movies = scrape_top10(top_apple_url, top_movies_section)
    top_apple_shows = scrape_top10(top_apple_url, top_shows_section)

    # Prime Video
    top_prime_movies = scrape_top10(top_prime_url, top_movies_section)
    top_prime_shows = scrape_top10(top_prime_url, top_shows_section)
    # Print the results
    if PRINT_LISTS:
        print_top_list("TOP Netflix Movies", top_netflix_movies)
        print_top_list("TOP Netflix Shows", top_netflix_shows)
        print_top_list("TOP Netflix Kids Movies", top_netflix_kids_movies)
        print_top_list("TOP Netflix Kids Shows", top_netflix_kids_shows)

        print_top_list("TOP HBO Movies", top_hbo_movies)
        print_top_list("TOP HBO Shows", top_hbo_shows)

        print_top_list("TOP Disney Overall", top_overrall)

        print_top_list("TOP Apple TV Movies", top_apple_movies)
        print_top_list("TOP Apple TV Shows", top_apple_shows)

        print_top_list("TOP Amazon Prime Video Movies", top_prime_movies)
        print_top_list("TOP Amazon Prime Video Shows", top_prime_shows)

    # Check the Trakt access token
    token_status = check_token()
    logging.info(f"Trakt access token status: {token_status}")
    if token_status is not True:
        return -1
    
    # Check necessary lists
    if check_lists() is True:
        logging.error("Failed to create necessary lists")
        return -1
    
    # List of streaming services and corresponding data
    streaming_services = [
        ("netflix", top_netflix_movies, top_netflix_shows, trakt_netflix_movies_list_slug, trakt_netflix_shows_list_slug),
        ("hbo", top_hbo_movies, top_hbo_shows, trakt_hbo_movies_list_slug, trakt_hbo_shows_list_slug),
        ("apple", top_apple_movies, top_apple_shows, trakt_apple_movies_list_slug, trakt_apple_shows_list_slug),
        ("prime", top_prime_movies, top_prime_shows, trakt_prime_movies_list_slug, trakt_prime_shows_list_slug)
    ]

    # Create and update lists for each streaming service
    for service, movies, shows, movies_slug, shows_slug in streaming_services:
        movies_update = create_type_trakt_list_payload(movies, "movie")
        shows_update = create_type_trakt_list_payload(shows, "show")
        
        update_list(movies_slug, movies_update)
        update_list(shows_slug, shows_update)

    # Handle Disney+ list as Disney stoped showing top movies and shows separately
    disney_update = create_mixed_trakt_list_payload(top_overrall)
    update_list(trakt_disney_list_slug, disney_update)

    # Handle kids' lists
    if KIDS_LIST:
        kids_streaming_services = [
            ("netflix", top_netflix_kids_movies, top_netflix_kids_shows, trakt_netflix_kids_movies_list_slug, trakt_netflix_kids_shows_list_slug)
        ]
    
        for service, movies, shows, movies_slug, shows_slug in kids_streaming_services:
            movies_update = create_type_trakt_list_payload(movies, "movie")
            shows_update = create_type_trakt_list_payload(shows, "show")

            update_list(movies_slug, movies_update)
            update_list(shows_slug, shows_update)

    logging.info("Finished updating lists")

if __name__ == "__main__":
    main()
