#!/usr/bin/env python3
# coding: utf-8

import logging

logging.basicConfig(level=logging.INFO)
import os
import json
import tqdm
from datetime import datetime

from scholarly import scholarly
from scholarly import ProxyGenerator

import pandas as pd

AUTHOR = ""
START_YEAR = 2014

PUBLICATIONS_PER_ARTICLE_PER_YEAR = {}
MISSING_PUB_YEAR = 0

# Setup caching
CACHE_FOLDER = "cache/"
if not os.path.exists(CACHE_FOLDER):
    os.makedirs(CACHE_FOLDER)

# Set up a ProxyGenerator object to use free proxies.
# This needs to be done only once per session.
#pg = ProxyGenerator()
#pg.FreeProxies()
#scholarly.use_proxy(pg)


# Retrieve author infos.
def retrieveAuthorInfos():
    print("[+] Retrieving author infos.")
    if os.path.exists(CACHE_FOLDER + "author.json"):
        with open(CACHE_FOLDER + "author.json", "r") as handle:
            return json.load(handle)
    else:
        infos = scholarly.fill(next(scholarly.search_author(AUTHOR)))
        with open(CACHE_FOLDER + "author.json", "w") as handle:
            json.dump(infos, handle)
        return infos


# Prepare citations per year dict.
def prepareCitationDict(publications):
    global PUBLICATIONS_PER_ARTICLE_PER_YEAR, MISSING_PUB_YEAR
    print("[+] Prepare citations per year dictionary.")
    for publication in publications:
        if publication["num_citations"] > 0:
            PUBLICATIONS_PER_ARTICLE_PER_YEAR[publication["bib"]["title"]] = {}
            for year in range(START_YEAR, datetime.now().year + 1):
                PUBLICATIONS_PER_ARTICLE_PER_YEAR[publication["bib"]["title"]][str(year)] = 0


# Retrieve citations per year.
def countCitations(publications):
    global PUBLICATIONS_PER_ARTICLE_PER_YEAR, MISSING_PUB_YEAR
    print("[+] Gathering citations.")
    for publication in tqdm.tqdm(publications):
        if publication["num_citations"] > 0:
            # Try from cache
            if os.path.exists(CACHE_FOLDER + publication["cites_id"][0] + ".json"):
                with open(CACHE_FOLDER + publication["cites_id"][0] + ".json", "r") as handle:
                    citations = json.load(handle)
            else:
                citations = list(scholarly.citedby(publication))
                with open(CACHE_FOLDER + publication["cites_id"][0] + ".json", "w") as handle:
                    json.dump(citations, handle)
            for citation in citations:
                try:
                    PUBLICATIONS_PER_ARTICLE_PER_YEAR[publication["bib"]["title"]][citation["bib"]["pub_year"]
                                                                                  ] += 1
                except KeyError as e:
                    MISSING_PUB_YEAR += 1


def main():
    infos = retrieveAuthorInfos()
    publications = infos["publications"]
    prepareCitationDict(publications)
    countCitations(publications)

    import matplotlib.pyplot as plt
    df = pd.DataFrame.from_dict(PUBLICATIONS_PER_ARTICLE_PER_YEAR)
    df.plot.bar(stacked=True)
    plt.show()


if __name__ == "__main__":
    main()
    import sys
    sys.exit()

with open("data.json", "w", encoding="utf-8") as handle:
    json.dump(PUBLICATIONS_PER_ARTICLE_PER_YEAR, handle, ensure_ascii=False, indent=4)
