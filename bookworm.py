import argparse
import os
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", required=True, help="URL of the first chapter")
    parser.add_argument(
        "-o", "--output", required=True, help="Output file to save the book to"
    )
    parser.add_argument(
        "-e",
        "--engine",
        choices=("auto", "requests", "playwright"),
        default="auto",
        help="HTML fetch engine to use",
    )
    return parser.parse_args()


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def ensure_output_path(output_path: str) -> None:
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def fetch_html_requests(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def fetch_html_playwright(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(1000)
        html = page.content()
        browser.close()
        return html


def extract_title(soup: BeautifulSoup) -> str | None:
    title = soup.find("h1")
    return title.get_text(strip=True) if title else None


def extract_content(soup: BeautifulSoup) -> str | None:
    container = soup.find("div", {"data-container": True})
    if container:
        text = container.get_text(separator="\n").strip()
    else:
        paragraphs = soup.select("main[data-reader-content] .node-doc p")
        if not paragraphs:
            return None
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)

    cleaned = "\n".join(line for line in text.splitlines() if line.strip())
    return cleaned or None


def extract_next_url(soup: BeautifulSoup, domain: str) -> str | None:
    next_link = soup.find("a", {"data-next-chapter-link": True})
    if next_link and next_link.has_attr("href"):
        return urljoin(domain, next_link["href"])

    candidates = soup.select("a.ty_a0.ty_cm[href*='/read/']")
    if candidates:
        return urljoin(domain, candidates[-1]["href"])

    return None


def parse_html(html: str, domain: str) -> tuple[str | None, str | None, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    title = extract_title(soup)
    content = extract_content(soup)
    next_url = extract_next_url(soup, domain)
    return title, content, next_url


def get_page_data(url: str, domain: str, engine: str):
    html = (
        fetch_html_requests(url)
        if engine == "requests"
        else fetch_html_playwright(url)
    )
    title, content, next_url = parse_html(html, domain)
    return title, content, next_url


def scrape_book(start_url: str, output: str, engine: str) -> None:
    ensure_output_path(output)
    current_url = start_url
    domain = extract_domain(current_url)

    try:
        with open(".current_url.txt", "r", encoding="utf-8") as f:
            tmp_url = f.readline().strip()
            if tmp_url:
                print(".current_url file found, resuming from last saved URL")
                current_url = tmp_url
    except FileNotFoundError:
        pass

    while current_url:
        time.sleep(3)
        print(f"Processing {current_url}...")

        try:
            if engine == "auto":
                title, content, next_url = get_page_data(
                    current_url, domain, "requests"
                )
                if not title or not content:
                    title, content, next_url = get_page_data(
                        current_url, domain, "playwright"
                    )
            else:
                title, content, next_url = get_page_data(current_url, domain, engine)

            if not title or not content:
                raise RuntimeError("Failed to extract chapter content")

            with open(output, "a", encoding="utf-8") as f:
                f.write("\n" + "-" * 20 + "\n")
                f.write(f"{title}\n\n")
                f.write(content)

            with open(".current_url.txt", "w", encoding="utf-8") as f:
                f.write(next_url or "")

            current_url = next_url
        except Exception as exc:
            print(f"Error while processing {current_url}: {exc}")
            break


if __name__ == "__main__":
    args = parse_args()
    scrape_book(args.url, args.output, args.engine)
