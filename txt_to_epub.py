import argparse
import html
import re
from ebooklib import epub


def parse_args():
    parser = argparse.ArgumentParser(description="Convert TXT file to EPUB")
    parser.add_argument("-i", "--input", required=True, help="Input TXT file")
    parser.add_argument("-o", "--output", required=True, help="Output EPUB file")
    parser.add_argument("-t", "--title", default="Untitled", help="Book title")
    parser.add_argument("-a", "--author", default="Unknown", help="Book author")
    parser.add_argument("-l", "--language", default="en", help="Book language code")
    return parser.parse_args()


def parse_chapters(content: str) -> list[tuple[str, str]]:
    """Parse TXT content into chapters using '--------------------' as separator."""
    separator = re.compile(r"\n-{20,}\n")
    parts = separator.split(content)

    chapters = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        lines = part.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        # Skip chapters with no content
        if not body:
            continue

        chapters.append((title or "Chapter", body))

    return chapters


def text_to_html(text: str) -> str:
    """Convert plain text to HTML, preserving paragraphs."""
    text = html.escape(text)
    paragraphs = re.split(r"\n\n+", text)
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if p:
            p = p.replace("\n", "<br/>")
            html_parts.append(f"<p>{p}</p>")

    # If no paragraphs found, wrap the whole text
    if not html_parts:
        text = text.strip()
        if text:
            html_parts.append(f"<p>{text.replace(chr(10), '<br/>')}</p>")
        else:
            html_parts.append("<p>&#160;</p>")  # Non-breaking space as fallback

    return "\n".join(html_parts)


def create_epub(chapters: list[tuple[str, str]], title: str, author: str, language: str) -> epub.EpubBook:
    """Create an EPUB book from chapters."""
    book = epub.EpubBook()
    book.set_title(title)
    book.add_author(author)
    book.set_language(language)

    epub_chapters = []
    for i, (chapter_title, chapter_body) in enumerate(chapters, 1):
        safe_title = html.escape(chapter_title)
        chapter = epub.EpubHtml(
            title=chapter_title,
            file_name=f"chapter_{i:04d}.xhtml",
            lang=language
        )
        body_content = text_to_html(chapter_body)
        html_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{safe_title}</title></head>
<body>
<h1>{safe_title}</h1>
{body_content}
</body>
</html>"""
        chapter.content = html_content.encode('utf-8')
        book.add_item(chapter)
        epub_chapters.append(chapter)

    book.toc = epub_chapters
    book.spine = ["nav"] + epub_chapters

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    return book


def txt_to_epub(input_path: str, output_path: str, title: str, author: str, language: str) -> None:
    """Convert a TXT file to EPUB format."""
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    chapters = parse_chapters(content)
    if not chapters:
        raise ValueError("No chapters found in input file")

    print(f"Found {len(chapters)} chapters")

    book = create_epub(chapters, title, author, language)
    epub.write_epub(output_path, book)
    print(f"EPUB written to {output_path}")


if __name__ == "__main__":
    args = parse_args()
    txt_to_epub(args.input, args.output, args.title, args.author, args.language)
