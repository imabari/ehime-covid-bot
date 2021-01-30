import os
import csv
import datetime
import pathlib
import re
import unicodedata

import json
import pdfplumber
import requests

def fetch_file(url, dir="."):

    p = pathlib.Path(dir, pathlib.PurePath(url).name)
    p.parent.mkdir(parents=True, exist_ok=True)

    r = requests.get(url)

    with p.open(mode="wb") as fw:
        fw.write(r.content)

    return p

p = fetch_file("https://www.pref.ehime.jp/h25500/kansen/documents/kennai_link.pdf", "data")

pdf = pdfplumber.open(p)

JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")
dt_now = datetime.datetime.now(JST).replace(tzinfo=None)

year = dt_now.year

for page in pdf.pages[::-1]:

    s = unicodedata.normalize("NFKC", page.extract_text())

    if s.startswith("県内における新型コロナウイルス感染症患者の発生状況について"):

        m = re.search("(\d{1,2})月(\d{1,2})日 +(\d{1,2})時現在", s)
        month, day, hour = map(int, m.groups())

        dt_date = datetime.datetime(year, month, day, hour)

        if dt_date > dt_now:
            dt_date = datetime.datetime(year - 1, month, day, hour)

        data = [int(i.replace(",", "")) for i in re.findall("([0-9,]+)人", s)]

        print(dt_date, data)

        if len(data) >= 9:

            if data[2] != data[3] + data[4]:
                print("医療機関の合計が違います")
            elif data[1] != data[2] + data[5]:
                print("入院中の合計が違います")
            elif data[0] != data[1] + data[6] + data[7] + data[8]:
                print("感染者累計が違います")
            
            result = [dt_date.isoformat()] + data

            p_csv = pathlib.Path("data", "latest.csv")

            with p_csv.open(mode="w") as fw:
                writer = csv.writer(fw, dialect="excel", lineterminator="\n")
                writer.writerow(result)

            url = os.environ["WEBAPPS"]
            headers = {"Content-Type": "application/json"}

            json_data = json.dumps({"data": [dt_date.isoformat()] + data})
            requests.post(url, json_data, headers=headers)

        break
