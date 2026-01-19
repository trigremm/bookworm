# Repository Guidelines

## Project Structure & Module Organization
- `bookworm.py` is the core scraping script with an auto engine (requests, Playwright fallback).
- `output/` contains generated text files. Resume state is stored in `.current_url.txt` in the repo root.
- Supporting files: `requirements.txt` for Python deps and `Makefile` for formatting and local HTTP serving.

## Build, Test, and Development Commands
- `python -m pip install -r requirements.txt` installs runtime dependencies.
- `python bookworm.py -u <first_chapter_url> -o output/book.txt` runs the scraper (auto engine).
- `python bookworm.py -u <first_chapter_url> -o output/book.txt -e playwright` forces Playwright.
- `make http_server` serves files on `http://localhost:8000/`.
- `make format` runs `black` and `isort` on the repository.

## Coding Style & Naming Conventions
- Python is formatted with `black` and imports are sorted with `isort`; keep code compatible with those tools.
- Use 4-space indentation and snake_case for functions and variables.
- Output files should live under `output/` and keep descriptive base names (e.g., `output/lotm__chapter-title.txt`).

## Testing Guidelines
- There is no automated test suite yet. If you add tests, place them in a `tests/` directory and name files `test_*.py`.
- Prefer small, deterministic tests that do not hit external sites unless explicitly marked as integration tests.

## Commit & Pull Request Guidelines
- Git history uses short, direct commit subjects (e.g., “update”, “file added”). Keep messages concise and imperative.
- PRs should include: purpose, how to run the script, and any new dependencies or output files produced.
- If behavior changes the scraping flow, include example URLs and sample output filenames.

## Configuration & Runtime Notes
- The scrapers maintain a `.current_url.txt` file to resume progress. Do not delete it mid-run unless you want a fresh start.
- Playwright runs headless Chromium with `--no-sandbox`; update cautiously if changing deployment environments.
