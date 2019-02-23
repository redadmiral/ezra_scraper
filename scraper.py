# This is a template for a Python scraper on morph.io (https://morph.io)
# including some code snippets below that you should find helpful

import requests_html
import re
import json
import locale
import datetime
import os

os.environ["SCRAPERWIKI_DATABASE_NAME"] = "sqlite:///data.sqlite"

import scraperwiki

# Read in a page

from requests_html import HTMLSession
session = HTMLSession()

site_url = 'https://ezra.de/chronik/'

r = session.get(site_url)
r.html.render(sleep = 5)

articles = r.html.find("article")
#articles = chronic.find("article")

singledate = re.compile("[0-9.]*")
timespan = re.compile("[0-9\.]*-[0-9\.]*")
month_year = re.compile("\w*\ [0-9]{4}")
month = re.compile("[A-Z][a-z]*")

last_year = 2000

locale.setlocale(locale.LC_ALL, "de_DE.UTF-8") #for encoding german month names

endDate = ""
startDate = ""

for article in articles:

    ## Parse dates
    date = article.find(".chronic__entry__date")
    if singledate.fullmatch(date[0].text):
        if timespan.match(date[0].text):
            startDate = datetime.datetime.strptime(date[0].text.split("-")[0], "%d.%m.%Y")
            print(last_year)
            last_year = startDate.year
            startDate = startDate.isoformat()
            endDate = datetime.datetime.strptime(date[0].text.split("-")[1], "%d.%m.%Y").isoformat()
        else:
            startDate = datetime.datetime.strptime(date[0].text, "%d.%m.%Y").isoformat()
    elif month.match(date[0].text):
        if month_year.match(date[0].text):
            startDate = datetime.datetime.strptime(date[0].text, "%B %Y").isoformat()
        else:
            startDate = datetime.datetime.strptime(date[0].text, "%B")
            startDate.replace(year = last_year) #year is not part of the article. It is assumed that the article was published in the same year as the last one.
            startDate = startDate.isoformat()

    ## Parse location:
    location = article.find(".chronic__entry__heading__location")[0].text.replace("Stadt ", "")

    ## Parse title
    title = article.find(".chronic__entry__heading__title")[0].text

    ## Parse content
    content = article.find("div.chronic__entry__content-wrapper > div > p")[0].text

    ## Parse source
    source_primary = "EZRA Chronik"
    source_uri_primary = "https://ezra.de/chronik/"

    if article.find(".chronic__entry__source"):
        source_secondary = article.find(".chronic__entry__source")[0].text.replace("Quelle: ", "")
        source_uri_secondary = article.find(".chronic__entry__source")[0].links
        source_uri_secondary = str(source_uri_secondary).replace("set()", "")


    uri = startDate + location
    uri.replace(" ", "_")

    ## Write data
    scraperwiki.sqlite.save(
        unique_keys=["uri"],
        data={
            "sources": json.dumps(
                [{"name": source_primary, "date": "", "url": source_uri_primary},
                {"name": source_secondary, "date": "", "url": source_uri_secondary}]
                ),
            "description": content,
            "startDate": startDate,
            "endDate": endDate,
            "locations": json.dumps({"subdivisions": [location, "Thüringen", "Germany"], "latitude": "", "longitude":""}),
            "iso3166_2": "DE-TH",
            "uri": uri,
            "motives": "",
            "contexts": "",
            "factums": "",
            "tags": ""
        },
        table_name="data",  # broken right now
)
