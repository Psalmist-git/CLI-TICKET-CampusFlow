import re
import html
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st


# Library-focused news sources
NEWS_SEARCHES = [
    {
        "name": "Library News",
        "query": "libraries OR librarians OR library services"
    },
    {
        "name": "Books and Publishing",
        "query": "books OR publishing OR authors OR book industry"
    },
    {
        "name": "Reading and Literacy",
        "query": "reading OR literacy OR reading culture"
    },
    {
        "name": "Research and Digital Libraries",
        "query": "digital libraries OR academic libraries OR research libraries"
    }
]


def build_news_feeds():
    """Build Google News RSS feeds for library-related topics."""

    feeds = []

    for item in NEWS_SEARCHES:
        params = {
            "q": f'{item["query"]} when:7d',
            "hl": "en",
            "gl": "US",
            "ceid": "US:en"
        }

        url = (
            "https://news.google.com/rss/search?"
            + urllib.parse.urlencode(params)
        )

        feeds.append({
            "name": item["name"],
            "url": url
        })

    return feeds


NEWS_FEEDS = build_news_feeds()


def clean_html(value):
    """Remove HTML tags and clean text."""

    if not value:
        return ""

    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def find_text(element, names):
    """Find an XML element by its local tag name."""

    for child in element.iter():
        tag = child.tag.split("}")[-1].lower()

        if tag in names:
            return child.text or ""

    return ""


def find_link(element):
    """Extract an article link from RSS or Atom."""

    for child in element:

        tag = child.tag.split("}")[-1].lower()

        if tag == "link":

            href = child.attrib.get("href")

            if href:
                return href

            if child.text:
                return child.text.strip()

    return ""


def find_image(element, description):
    """Find an article image where the feed provides one."""

    for child in element.iter():

        tag = child.tag.split("}")[-1].lower()

        if tag in {"thumbnail", "content"}:

            image_url = (
                child.attrib.get("url")
                or child.attrib.get("href")
            )

            if image_url and image_url.startswith("https://"):
                return image_url

    for child in element:

        if child.tag.split("}")[-1].lower() == "enclosure":

            image_url = child.attrib.get("url", "")
            media_type = child.attrib.get("type", "")

            if (
                image_url.startswith("https://")
                and media_type.startswith("image/")
            ):
                return image_url

    match = re.search(
        r"<img[^>]+src=[\"']([^\"']+)[\"']",
        description,
        re.IGNORECASE
    )

    if match:

        image_url = html.unescape(match.group(1))

        if image_url.startswith("https://"):
            return image_url

    return None


def parse_publication_date(value):
    """Convert a published date into a sortable timestamp."""

    if not value:
        return None

    try:

        published = parsedate_to_datetime(value)

        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)

        return published.isoformat()

    except (TypeError, ValueError, OverflowError):

        try:

            published = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)

            return published.isoformat()

        except (TypeError, ValueError):
            return None


def fetch_feed(feed):
    """Download and parse one RSS or Atom feed."""

    request = urllib.request.Request(
        feed["url"],
        headers={
            "User-Agent": "Mozilla/5.0 CampusFlow Library News Reader"
        }
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)

    articles = []

    for element in root.iter():

        tag = element.tag.split("}")[-1].lower()

        if tag not in {"item", "entry"}:
            continue

        title = find_text(element, {"title"})
        link = find_link(element)

        raw_description = find_text(
            element,
            {"description", "summary", "encoded"}
        )

        published = find_text(
            element,
            {"pubdate", "published", "updated", "date"}
        )

        if not title or not link:
            continue

        title = clean_html(title)
        description = clean_html(raw_description)

        articles.append({
            "title": title,
            "description": description[:450],
            "link": link,
            "source": feed["name"],
            "published": parse_publication_date(published),
            "image": find_image(element, raw_description)
        })

    return articles


@st.cache_data(ttl=600, show_spinner=False)
def get_library_news():
    """
    Collect library-related news from multiple feeds.

    Sources are fetched concurrently.
    Results are cached for ten minutes.
    """

    all_articles = []
    failed_sources = []

    with ThreadPoolExecutor(max_workers=4) as executor:

        future_sources = {
            executor.submit(fetch_feed, feed): feed["name"]
            for feed in NEWS_FEEDS
        }

        for future in as_completed(future_sources):

            source_name = future_sources[future]

            try:
                all_articles.extend(future.result())

            except Exception as error:

                failed_sources.append(source_name)

                print(
                    f"Library news feed error ({source_name}): "
                    f"{type(error).__name__}"
                )

    unique_articles = {}
    now = datetime.now(timezone.utc)

    for article in all_articles:

        title_key = article["title"].lower().strip()

        if not title_key:
            continue

        published = article.get("published")

        if published:

            try:

                published_date = datetime.fromisoformat(published)

                if published_date.tzinfo is None:
                    published_date = published_date.replace(
                        tzinfo=timezone.utc
                    )

                age_days = (
                    now - published_date
                ).total_seconds() / 86400

                if age_days > 14:
                    continue

            except (ValueError, TypeError):
                pass

        if title_key not in unique_articles:
            unique_articles[title_key] = article

    sorted_articles = sorted(
        unique_articles.values(),
        key=lambda article: article.get("published") or "",
        reverse=True
    )

    return {
        "articles": sorted_articles[:24],
        "failed_sources": failed_sources,
        "updated_at": now.isoformat()
    }


# Backward compatibility:
# Existing app.py calls to get_education_news() will still work.
def get_education_news():
    return get_library_news()