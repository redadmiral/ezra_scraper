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
r.html.render(sleep = 5) ## Rendering takes a bit.

articles = r.html.find("article")
#articles = chronic.find("article")

singledate = re.compile("[0-9.]*")
timespan = re.compile("[0-9\.]*-[0-9\.]*")
month_year = re.compile("\w*\ [0-9]{4}")
month = re.compile("[A-Z][a-z]*")

locale.setlocale(locale.LC_ALL, "de_DE.UTF-8") #mapping german month names

endDate = None
startDate = None
last_year = 0

for article in articles:
    ## Parse dates
    date = article.find(".chronic__entry__date")
    if singledate.fullmatch(date[0].text) or timespan.fullmatch(date[0].text):
        if timespan.fullmatch(date[0].text):
            startDate = datetime.datetime.strptime(date[0].text.split("-")[0], "%d.%m.%Y")
            last_year = startDate.year
            startDate = startDate.isoformat()
            endDate = datetime.datetime.strptime(date[0].text.split("-")[1], "%d.%m.%Y").isoformat()
        else:
            startDate = datetime.datetime.strptime(date[0].text, "%d.%m.%Y")
            last_year = startDate.year
            startDate = startDate.isoformat()
            endDate = ""
    elif month.match(date[0].text):
        if month_year.match(date[0].text):
            startDate = datetime.datetime.strptime(date[0].text, "%B %Y")
            last_year = startDate.year
            startDate = startDate.isoformat()
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

    sources = []
    sources.append({"name": "EZRA Chronik", "date": "", "url": "https://ezra.de/chronik/"})

    if article.find(".chronic__entry__source"):
        source_secondary = article.find(".chronic__entry__source")[0].text.replace("Quelle: ", "")
        source_uri_secondary = article.find(".chronic__entry__source")[0].links
        if not source_uri_secondary:
            source_uri_secondary = ""
        else:
            source_uri_secondary = next(iter(source_uri_secondary))
        sources.append({"name": source_secondary, "date": "", "url": source_uri_secondary})


    uri = startDate + location
    uri.replace(" ", "_")

    ## Write DB

    scraperwiki.sqlite.save(
        unique_keys=["uri"],
        data={"description": content, "startDate": startDate, "endDate": endDate, "iso3166_2": "DE-TH", "uri": uri},
        table_name="data",
    )

    scraperwiki.sqlite.save(
        unique_keys=["reportURI"],
        data={"subdivisions": location, "reportURI": uri, "latitude": "", "longitude": ""},
        table_name="location",
    )

    for s in sources:
        scraperwiki.sqlite.save(
            unique_keys=["reportURI"],
            data={"publishedDate": s["date"], "name": s["name"], "reportURI": uri, "url": s["url"]},
            table_name="source",
            )
