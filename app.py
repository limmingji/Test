#!/usr/bin/env python3
"""Fetch headlines from NewsNow and summarize linked stories."""

from __future__ import annotations

import argparse
import re
import textwrap
from collections import Counter
from html import unescape
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


USER_AGENT = "NewsNowSummaryBot/1.0 (+https://example.com)"
DEFAULT_URL = "https://www.newsnow.com/"
STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "but",
    "by",
    "can",
    "could",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "his",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "may",
    "more",
    "most",
    "new",
    "no",
    "not",
    "of",
    "on",
    "one",
    "or",
    "other",
    "our",
    "out",
    "over",
    "said",
    "she",
    "should",
    "so",
    "some",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "they",
    "this",
    "to",
    "up",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "will",
    "with",
    "would",
    "you",
    "your",
}


def fetch_html(url: str, timeout: int = 15) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    return response.text


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_headlines(html: str, base_url: str, limit: int) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    for anchor in soup.select("a[href]"):
        title = normalize_whitespace(anchor.get_text(" ", strip=True))
        href = anchor.get("href")
        if not title or not href:
            continue
        if len(title) < 30:
            continue

        absolute = urljoin(base_url, href)
        key = (title, absolute)
        if key in seen:
            continue
        seen.add(key)
        links.append({"title": unescape(title), "url": absolute})
        if len(links) >= limit:
            break

    return links


def extract_story_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    selectors = [
        "article",
        "main",
        "div[itemprop='articleBody']",
        "div.story-body",
        "div.article-body",
        "div.content",
    ]

    paragraphs = []
    for selector in selectors:
        container = soup.select_one(selector)
        if not container:
            continue
        paragraphs = [
            normalize_whitespace(p.get_text(" ", strip=True))
            for p in container.select("p")
            if normalize_whitespace(p.get_text(" ", strip=True))
        ]
        if paragraphs:
            break

    if not paragraphs:
        paragraphs = [
            normalize_whitespace(p.get_text(" ", strip=True))
            for p in soup.select("p")
            if normalize_whitespace(p.get_text(" ", strip=True))
        ]

    return "\n".join(paragraphs)


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def summarize(text: str, max_sentences: int = 3) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return "Summary unavailable."

    words = re.findall(r"[A-Za-z']+", text.lower())
    meaningful_words = [word for word in words if word not in STOPWORDS]
    scores = Counter(meaningful_words)

    ranked = []
    for idx, sentence in enumerate(sentences):
        tokens = re.findall(r"[A-Za-z']+", sentence.lower())
        score = sum(scores[token] for token in tokens if token not in STOPWORDS)
        ranked.append((score, idx, sentence))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    best = sorted(ranked[:max_sentences], key=lambda item: item[1])
    summary = " ".join(sentence for _, _, sentence in best)
    return summary or "Summary unavailable."


def format_story(story: dict[str, str], summary: str) -> str:
    wrapped = textwrap.fill(summary, width=88)
    return (
        f"Headline: {story['title']}\n"
        f"URL: {story['url']}\n"
        f"Summary: {wrapped}\n"
    )


def build_report(url: str, limit: int, summary_sentences: int) -> str:
    html = fetch_html(url)
    headlines = extract_headlines(html, url, limit)

    output_lines = [f"NewsNow summary from {url}", "=" * 88, ""]
    if not headlines:
        output_lines.append("No headlines found. The site structure may have changed.")
        return "\n".join(output_lines)

    for entry in headlines:
        article_html = fetch_html(entry["url"])
        story_text = extract_story_text(article_html)
        summary = summarize(story_text, max_sentences=summary_sentences)
        output_lines.append(format_story(entry, summary))

    return "\n".join(output_lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract headlines and summarize stories from NewsNow.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="NewsNow page to scrape (default: https://www.newsnow.com/)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of headlines to summarize.",
    )
    parser.add_argument(
        "--summary-sentences",
        type=int,
        default=3,
        help="Number of sentences to include in each summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.url, args.limit, args.summary_sentences)
    print(report)


if __name__ == "__main__":
    main()
