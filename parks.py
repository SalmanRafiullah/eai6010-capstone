import re
from collections import Counter
import requests
import geopandas as gpd
from bs4 import BeautifulSoup

BASE_URL = "https://www.mass.gov"


def parse_park_list():
    page = requests.get(
        f"{BASE_URL}/guides/alphabetical-list-of-massachusetts-state-parks"
    )
    soup = BeautifulSoup(page.text, "html.parser")
    park_table_list = soup.find(class_="ma__stacked-row")
    links = park_table_list.find_all("a")[:-4]
    parks_links = []

    for a_link in links:
        link = a_link.get("href")

        if "locations" in link:
            parks_links.append({
                "park_name": a_link.contents[0],
                "url": f"{BASE_URL}{a_link.get('href')}"
            })

    return parks_links


def parse_park_zip_code(url):
    page_park = requests.get(url)
    soup_park = BeautifulSoup(page_park.text, "html.parser")
    contact_group_tag = soup_park.find(class_="ma__contact-group__address")
    address_content = contact_group_tag.contents[0]
    result = re.search(r'[0-9]{5}', address_content)
    return result.group(0)


def parse_zip_codes(park_list):
    for park in park_list:
        zip_code = parse_park_zip_code(park["url"])
        park["zip_code"] = zip_code


if __name__ == "__main__":
    parks = parse_park_list()
    parse_zip_codes(parks)

    working_df = gpd.read_file("project data/working.geojson")
    zip_code_park_counter = Counter(map(lambda x: x["zip_code"], parks))
    working_df["state_parks"] = working_df.apply(
        lambda x: zip_code_park_counter[x["GEOID10"]], axis=1
    )
    working_df[["ZipCode", "state_parks"]].to_csv("project data/state_parks.csv")
