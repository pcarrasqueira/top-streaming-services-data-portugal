import requests
from bs4 import BeautifulSoup

# Function to scrape movie or show data based in the section title
def scrape_top10(section_title):
    data = []

    # Get the webpage content
    url = "https://flixpatrol.com/top10/netflix/portugal/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")

        
    # Locate the correct section using 'h3' and the title
    section_header = soup.find("h3", text=section_title)
    # Check if the section was found
    if section_header:
        # Find the next div after the section header
        section_div = section_header.find_next("div", class_="card")
        tbody = section_div.find("tbody")  # Locate the table body within the div
        rows = tbody.find_all("tr")
        
        for row in rows:
            rank = row.find("td", class_="table-td w-12 font-semibold text-right text-gray-500 table-hover:text-gray-400").get_text(strip=True)  # Get the rank
            title = row.find("a").get_text(strip=True)  # Get the movie/show title
            data.append((rank, title))
                
    return data

# Extract Movies and TV Shows
top_movies = scrape_top10("TOP 10 Movies")
top_shows = scrape_top10("TOP 10 TV Shows")

# Print the results
print("TOP MOVIES")
for rank, title in top_movies:
    print(f"{rank}: {title}")

print("TOP Shows")
for rank, title in top_shows:
    print(f"{rank}: {title}")
