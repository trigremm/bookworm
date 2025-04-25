import argparse
import time

import requests
from bs4 import BeautifulSoup

d = """
start_url = 'https://ranobelib.me/ru/20818--lord-of-the-mysteries/read/v6/c1200?bid=18695'
output = 'output/lotm/lotm.txt'
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", required=True, help="URL of the first chapter")
    parser.add_argument(
        "-o", "--output", required=True, help="Output file to save the book to"
    )

    args = parser.parse_args()
    url, output = args.url, args.output

    return url, output


def scrape_book(start_url, output):
    current_url = start_url

    try:
        tmp_url = open(".current_url.txt", "r").readline().strip()
        print(".current_url file found, processing from last saved URL")
    except:  # noqa
        tmp_url = None

    if tmp_url:
        current_url = tmp_url

    while current_url:
        time.sleep(4)
        print(f"Processing {current_url}...")

        response = requests.get(current_url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the chapter title and content
        chapter_title = soup.find("h1").text.strip()
        chapter_content = (
            soup.find("div", {"data-container": True}).get_text(separator="\n").strip()
        )
        chapter_content = "\n".join(
            line for line in chapter_content.splitlines() if line.strip()
        )

        with open(output, "a", encoding="utf-8") as file:
            # Save to a text file
            file.write("\n" + "-" * 20 + "\n")
            file.write(chapter_title + "\n\n")
            file.write(chapter_content)

        # Find the URL of the next chapter
        next_link = soup.find("a", {"data-next-chapter-link": True})
        if next_link and "href" in next_link.attrs:
            current_url = next_link["href"]
        else:
            current_url = None

        with open(".current_url.txt", "w") as file:
            file.write(current_url)
    return True


if __name__ == "__main__":
    url, output = parse_args()
    flag = False
    counter = 0
    while not flag:
        try:
            flag = scrape_book(url, output)
        except:  # noqa
            flag = False
        counter += 1
        print(f"{counter=}")
