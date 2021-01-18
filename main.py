import datetime
import os
import pathlib
import re
import unicodedata
from urllib.parse import urljoin

import pdfbox
import requests
import tweepy
from bs4 import BeautifulSoup


def fetch_soup(url, parser="html.parser"):

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    soup = BeautifulSoup(r.content, parser)

    return soup


def fetch_file(url):

    r = requests.get(url)

    p = pathlib.Path(pathlib.PurePath(url).name)

    with p.open(mode="wb") as fw:
        fw.write(r.content)

    return p


url = "https://www.pref.ehime.jp/h25500/kansen/covid19.html"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
}

JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")
dt_now = datetime.datetime.now(JST).date()

soup = fetch_soup(url)

for i in soup.select("div#tmp_contents > ul > li > a"):

    title = i.get_text(strip=True)

    link = ""

    if "新型コロナウイルスの感染の確認" in title:

        print(title)

        m_dt = re.search("(\d{1,2})月(\d{1,2})日公表分", title)

        month, day = map(int, m_dt.groups())
        year = dt_now.year

        dt_update = datetime.date(year, month, day)

        if dt_now == dt_update:

            link = urljoin(url, i.get("href"))

            pdf_file = fetch_file(link)

            p = pdfbox.PDFBox()

            p.extract_text(pdf_file, sort=True)

            p.pdf_to_images(pdf_file, imageType="png", dpi=200)

            txt_file = pdf_file.with_suffix(".txt")
            png_file = pdf_file.with_name(pdf_file.name.replace(".pdf", "1.png"))

            with txt_file.open() as fr:
                temp = fr.read()

            text = unicodedata.normalize("NFKC", temp)

            m = re.search("昨日(.+)、県内で新型コロナウイルスの陽性者が(.+)名確認されました。", text)

            if m:

                s = m.group(0).replace(" ", "")

                twit = f"新型コロナウイルスの感染の確認について\n{s}\n{link}\n\n#愛媛県 #新型コロナ"

                consumer_key = os.environ["CONSUMER_KEY"]
                consumer_secret = os.environ["CONSUMER_SECRET"]
                access_token = os.environ["ACCESS_TOKEN"]
                access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

                auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
                auth.set_access_token(access_token, access_token_secret)

                api = tweepy.API(auth)
                api.update_with_media(status=twit, filename=str(png_file))
                
            break
