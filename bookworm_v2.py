import argparse
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from slugify import slugify


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", required=True, help="URL of the first chapter")
    parser.add_argument("-o", "--output", required=True, help="Output file base name")
    return parser.parse_args()


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_page_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(1000)
        html = page.content()
        browser.close()
        return html


def scrape_book(start_url, output_base):
    current_url = start_url
    domain = extract_domain(current_url)
    counter = 0

    try:
        with open(".current_url.txt", "r", encoding="utf-8") as f:
            tmp_url = f.readline().strip()
            print(".current_url file found, resuming from last saved URL")
            if tmp_url:
                current_url = tmp_url
    except FileNotFoundError:
        pass

    while current_url:
        time.sleep(3)
        print(f"Processing {current_url}...")

        try:
            html = get_page_html(current_url)
            soup = BeautifulSoup(html, "html.parser")

            title = soup.select_one("h1").get_text(strip=True)

            paragraphs = soup.select("main[data-reader-content] .node-doc p")
            text = "\n".join(p.get_text(strip=True) for p in paragraphs)

            # Generate current output file name
            if counter % 10 == 0:
                current_file = f"{output_base}__{slugify(title)}.txt"
                open(current_file, "w", encoding="utf-8")

            # Write to file
            with open(current_file, "a", encoding="utf-8") as f:
                f.write(f"{title}\n{'=' * len(title)}\n{text}\n\n\n")

            # Move to next chapter
            next_link = soup.select("a.ty_a0.ty_cm[href*='/read/']")[-1]
            if next_link and next_link.has_attr("href"):
                next_url = domain + next_link["href"]
            else:
                print("❌ No next chapter link found. Stopping.")
                break

            counter += 1
            if counter % 10 == 0:
                with open(".current_url.txt", "w", encoding="utf-8") as f:
                    f.write(next_url)

            current_url = next_url

        except Exception as e:
            print(f"❌ Error while processing {current_url}: {e}")
            break


if __name__ == "__main__":
    args = parse_args()
    scrape_book(args.url, args.output)
