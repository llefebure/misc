"""Scrapes the Motley Fool for earnings calls dating back to a specific date of
interest"""
import pandas as pd
import re
import requests
import time
from bs4 import BeautifulSoup
from collections import defaultdict
from dateutil.parser import parse
from tqdm import tqdm
from urllib.parse import urljoin


def extract_date(text):
    date_re = \
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Oct|Nov|Dec)\.? \d{1,2}, (2019|2020)"
    match = re.search(date_re, text)
    if match:
        return match.group(0)
    else:
        return None


def find_url_metadata(already_scraped, start_date="Jan 1, 2020"):
    all_earnings_calls = []
    i = 1
    # Boolean to track whether we've hit our start date or an item that we've
    # already scraped
    stop = False
    while not stop:
        url = f"https://www.fool.com/earnings-call-transcripts/?page={i}"
        response = requests.get(url)
        page = response.text
        soup = BeautifulSoup(page, features="lxml")
        articles = soup.find("div", "list-content").find_all("a")
        for _, article in enumerate(articles):
            try:
                text = article.find("div", {"class": "text"})
                url = urljoin("https://www.fool.com/", article["href"])
                title = text.find("h4").text
                author, date = text.find("div").text.split(" | ")
                description = text.find("p").text
                if parse(date) < parse(start_date) or url in already_scraped:
                    stop = True
                    break
                all_earnings_calls.append({
                    "url": url,
                    "title": title,
                    "author": author,
                    "transcribed_date": date,
                    "description": description
                })
            except:
                print("Failed to parse ", str(article))
                pass
        i += 1
    return pd.DataFrame(all_earnings_calls)


def _parse_url(url):
    response = requests.get(url)
    page = response.text
    soup = BeautifulSoup(page)
    try:
        content = soup.find("span", {"class": "article-content"})
        name = content.find("strong").text
        ticker = content.find("span", {"class": "ticker"}).text.strip("()")
        all_text_tags = list(content.find_all(["p", "h2"]))
        current_heading = "top"
        all_text_segmented = defaultdict(list)
        for text_chunk in all_text_tags:
            if text_chunk.name == "h2":
                current_heading = text_chunk.text.strip(":").lower()
                current_heading = current_heading.replace("&", "and")
                current_heading = current_heading.replace(" ", "_")
            else:
                all_text_segmented[current_heading].append(text_chunk.text)
        all_text_segmented_joined = {
            k: "\n\n".join(v) for k, v in all_text_segmented.items()}
        date = extract_date(all_text_segmented_joined.get("top", ""))
    except:
        name = ""
        ticker = ""
        all_text_segmented_joined = {}
        date = None
    expected = [
        "top", "prepared_remarks", "questions_and_answers", "call_participants"]
    return dict(
        {k: all_text_segmented_joined.get(k, "") for k in expected},
        name=name,
        ticker=ticker,
        date=date
    )


if __name__ == "__main__":
    # Gather URLs
    try:
        df = pd.read_csv("data/urls.csv")
        already_scraped = set(df.url)
        append = True
    except FileNotFoundError:
        already_scraped = set()
        append = False
    df = find_url_metadata(already_scraped)
    df.to_csv(
        "data/urls.csv",
        mode="a" if append else "w",
        header=not append,
        index=False)

    # Scrape each URL
    try:
        earnings_calls = pd.read_csv("data/earnings_calls.csv")
        append = True
    except:
        earnings_calls = None
        append = False
    tqdm.pandas()
    res = df.url.progress_apply(_parse_url)
    res = res.apply(pd.Series)
    final = pd.concat([df, res], axis=1)
    final.to_csv(
        "data/earnings_calls.csv",
        mode="a" if append else "w",
        header=not append,
        index=False)
