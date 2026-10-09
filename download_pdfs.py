"""Download the Member 3 public legal PDF corpus from India Code."""

from __future__ import annotations

from pathlib import Path
import re
import textwrap

import fitz
import requests


CORPUS_DIR = Path("corpus")
CORPUS_DIR.mkdir(exist_ok=True)

PDFS = [
    {
        "filename": "wages_act_2019.pdf",
        "url": "https://www.indiacode.nic.in/bitstream/123456789/15793/1/aA2019-29.pdf",
        "label": "The Code on Wages, 2019",
    },
    {
        "filename": "shops_establishments_act.pdf",
        "url": "https://www.indiacode.nic.in/bitstream/123456789/19710/1/201761.pdf",
        "fallback_url": "https://indiankanoon.org/doc/139822642/",
        "label": "Maharashtra Shops and Establishments Act, 2017",
    },
    {
        "filename": "consumer_protection_act_2019.pdf",
        "url": "https://www.indiacode.nic.in/bitstream/123456789/16939/1/a2019-35.pdf",
        "label": "Consumer Protection Act, 2019",
    },
    {
        "filename": "domestic_violence_act_2005.pdf",
        "url": "https://www.indiacode.nic.in/bitstream/123456789/2021/5/A2005-43.pdf",
        "label": "Protection of Women from Domestic Violence Act, 2005",
    },
]


def html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h[1-6]>", "\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def write_text_pdf(target: Path, title: str, text: str) -> None:
    doc = fitz.open()
    lines = [title, ""]
    for paragraph in text.splitlines():
        wrapped = textwrap.wrap(paragraph, width=95) or [""]
        lines.extend(wrapped)

    per_page = 48
    for start in range(0, len(lines), per_page):
        page = doc.new_page(width=595, height=842)
        page.insert_text(
            (40, 40),
            "\n".join(lines[start:start + per_page]),
            fontsize=9,
            fontname="courier",
        )
    doc.save(target)
    doc.close()


def download_pdf(filename: str, url: str, label: str, fallback_url: str | None = None) -> bool:
    print(f"Downloading {label}...")
    response = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})

    content_type = response.headers.get("content-type", "").lower()
    content = response.content
    target = CORPUS_DIR / filename
    if response.ok and ("pdf" in content_type or content.startswith(b"%PDF")):
        target.write_bytes(content)
        print(f"Saved {target} ({len(content):,} bytes)")
        return True

    if not fallback_url:
        response.raise_for_status()
        raise ValueError(f"URL did not return a PDF: {url}")

    print(f"Official PDF unavailable; creating PDF from public text at {fallback_url}")
    fallback = requests.get(fallback_url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    fallback.raise_for_status()
    text = html_to_text(fallback.text)
    if "maharashtra shops" not in text.lower() and label.lower() not in text.lower():
        raise ValueError(f"Fallback page did not contain expected act text: {fallback_url}")
    write_text_pdf(target, label, text)
    print(f"Saved {target} from fallback public text ({target.stat().st_size:,} bytes)")
    return True


def main() -> int:
    failures = 0
    for item in PDFS:
        try:
            download_pdf(**item)
        except Exception as exc:
            failures += 1
            print(f"Warning: failed to download {item['filename']}: {exc}")

    if failures:
        print(f"Download completed with {failures} failure(s).")
        return 1

    print("Download completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
