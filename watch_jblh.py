#!/usr/bin/env python3
"""
Wächter für die Jugendbundesliga-Spielpläne des VfL Horneburg.

Die JBLH liegt beim DHB und wandert gerade nach Handball360; auf handball.net
sind die Termine für 26/27 noch nicht eingespielt. Dieses Skript prüft
regelmässig, ob sie aufgetaucht sind, und meldet sich genau dann.

Wöchentlich laufen lassen, z.B.:
    0 8 * * 1  /usr/bin/python3 /pfad/watch_jblh.py
"""
import json, os, re, sys
import requests
from bs4 import BeautifulSoup

STATE = os.path.expanduser("~/.jblh_watch.json")
UA = {"User-Agent": "Mozilla/5.0 (Heimspielkalender Steinkirchen)"}

# Vereins-Newsfeed: dort erscheint der Spielplan erfahrungsgemäss zuerst
FEED = "https://vfl-horneburg.de/category/handball_news/feed/"
SIGNALS = re.compile(r"spielplan|termine|saisonstart|auftakt|heimspiel", re.I)

# handball.net-Ligaseiten (rendern clientseitig, deshalb nur Roh-Check)
LEAGUES = {
    "2. JBLH mA Nord": "https://www.handball.net/jblh-a-jugend-maennlich",
    "JBLH mB":         "https://www.handball.net/jblh-b-jugend-maennlich",
}


def load():
    try:
        return json.load(open(STATE))
    except Exception:
        return {"seen": []}


def save(s):
    json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=1)


def check_feed():
    hits = []
    try:
        r = requests.get(FEED, headers=UA, timeout=30)
        r.encoding = "utf-8"
        for it in BeautifulSoup(r.text, "xml").find_all("item"):
            title = it.title.get_text()
            if SIGNALS.search(title):
                hits.append((title, it.link.get_text()))
    except Exception as e:
        print(f"Feed nicht erreichbar: {e}", file=sys.stderr)
    return hits


def check_handballnet():
    hits = []
    for name, url in LEAGUES.items():
        try:
            html = requests.get(url, headers=UA, timeout=30).text
            if "Horneburg" in html:
                hits.append((name, url))
        except Exception:
            pass
    return hits


def main():
    state = load()
    seen = set(state["seen"])
    news = []

    for title, link in check_feed():
        if link not in seen:
            news.append(f"Vereins-News: {title}\n  {link}")
            seen.add(link)

    for name, url in check_handballnet():
        key = "hbnet:" + name
        if key not in seen:
            news.append(f"handball.net liefert jetzt Daten für {name}\n  {url}")
            seen.add(key)

    state["seen"] = sorted(seen)
    save(state)

    if news:
        print("JBLH-Spielpläne: es gibt Neues.\n")
        print("\n\n".join(news))
        print("\nDanach: ICS-URL in collect_heimspiele.py unter ICS_FEEDS "
              "eintragen und das Skript neu laufen lassen.")
    else:
        print("Noch nichts Neues zur Jugendbundesliga.")


if __name__ == "__main__":
    main()
