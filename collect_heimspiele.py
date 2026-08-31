#!/usr/bin/env python3
"""
Handball-Heimspiel-Collector fuer den Umkreis Steinkirchen (21720), suedlich der Elbe.
Quelle: nuLiga HVNB (Handballverband Niedersachsen-Bremen).
"""
import json, re, time, math, sys
import requests
from bs4 import BeautifulSoup
import pgeocode

BASE = "https://hvnb-handball.liga.nu/cgi-bin/WebObjects/nuLigaHBDE.woa/wa"
CHAMP = "HVNB 26/27"
HOME_PLZ = "21720"
RADIUS_KM = 30.0

# Staffeln ab Oberliga aufwaerts, Maenner + maennliche Jugend A/B
GROUPS = {
    489670: ("Regionalliga Nord",       "Herren", 2),
    489136: ("Oberliga Nord",           "Herren", 3),
    489112: ("Oberliga Sued",           "Herren", 3),
    489677: ("Regionalliga MJA",        "A-Jugend m", 2),
    489104: ("Oberliga MJA Nordost",    "A-Jugend m", 3),
    489152: ("Oberliga MJA West",       "A-Jugend m", 3),
    489717: ("Oberliga MJA Sued",       "A-Jugend m", 3),
    489124: ("Regionalliga MJB",        "B-Jugend m", 2),
    489488: ("Oberliga MJB Ost",        "B-Jugend m", 3),
    489568: ("Oberliga MJB West",       "B-Jugend m", 3),
    489327: ("Oberliga MJB Sued",       "B-Jugend m", 3),
}

S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (Heimspielkalender Steinkirchen)"

# Wettbewerbe oberhalb der HVNB-Ebene (Jugendbundesliga, 3. Liga).
# Die stehen nicht in nuLiga. handball.net bietet pro Mannschaft einen
# "Kalender abonnieren"-Link – diese ICS-URL hier eintragen, dann wandert
# der Spielplan automatisch mit ins Ergebnis.
ICS_FEEDS = [
    # {"url": "https://...ics", "liga": "2. JBLH Nord", "kategorie": "A-Jugend m",
    #  "stufe": 1, "heim": "VfL Horneburg", "halle": "Horneburg, SH 1",
    #  "strasse": "Hermannstraße 27", "plz": "21640", "ort": "Horneburg"},
]


def from_ics(feed):
    """Heimspiele aus einem ICS-Feed ziehen (handball.net 'Kalender abonnieren')."""
    txt = fetch(feed["url"]).replace("\r\n ", "").replace("\n ", "")
    out = []
    for block in txt.split("BEGIN:VEVENT")[1:]:
        ds = re.search(r"DTSTART[^:]*:(\d{8})T(\d{4})", block)
        su = re.search(r"SUMMARY:(.+)", block)
        if not (ds and su):
            continue
        d, t = ds.group(1), ds.group(2)
        title = su.group(1).strip()
        parts = re.split(r"\s+[-–:]\s+|\s+vs\.?\s+", title)
        if len(parts) < 2:
            continue
        heim, gast = parts[0].strip(), parts[1].strip()
        if feed["heim"].lower() not in heim.lower():
            continue          # nur Heimspiele
        lat, lon, _ = geo(feed["plz"])
        hlat, hlon, _ = geo(HOME_PLZ)
        out.append({
            "datum": f"{d[6:8]}.{d[4:6]}.{d[0:4]}", "zeit": f"{t[:2]}:{t[2:]}",
            "nr": "", "liga": feed["liga"], "kategorie": feed["kategorie"],
            "stufe": feed["stufe"], "heim": feed["heim"], "gast": gast,
            "halle": feed["halle"], "strasse": feed.get("strasse"),
            "plz": feed["plz"], "ort": feed["ort"],
            "lat": round(lat, 5), "lon": round(lon, 5),
            "entfernung_km": round(haversine(hlat, hlon, lat, lon), 1),
            "quelle": feed["url"],
        })
    return out

nomi = pgeocode.Nominatim("de")
_geo_cache = {}

def geo(plz):
    if plz in _geo_cache:
        return _geo_cache[plz]
    r = nomi.query_postal_code(plz)
    try:
        lat, lon, state = float(r["latitude"]), float(r["longitude"]), str(r["state_name"])
    except Exception:
        lat = lon = float("nan"); state = ""
    _geo_cache[plz] = (lat, lon, state)
    return _geo_cache[plz]

def haversine(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(h))

def fetch(url, params=None):
    for attempt in range(3):
        try:
            r = S.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)

_loc_cache = {}

def hall(loc_id):
    """Hallenname + PLZ/Ort ueber courtInfo aufloesen."""
    if loc_id in _loc_cache:
        return _loc_cache[loc_id]
    html = fetch(f"{BASE}/courtInfo",
                 {"federation": "HVNB", "roundTyp": "0",
                  "championship": CHAMP, "location": loc_id})
    soup = BeautifulSoup(html, "lxml")
    lines = [l.strip() for l in soup.get_text("\n").split("\n") if l.strip()]
    name = strasse = plz = ort = None
    for i, l in enumerate(lines):
        m = re.match(r"^(.+?)\s*\((\d{5,7})\)$", l)
        if m and not name:
            name = m.group(1).strip()
        if l.startswith("Hallenadresse"):
            rest = [x for x in lines[i+1:i+6]]
            if rest:
                strasse = rest[0]
            for r in rest:
                mm = re.match(r"^(\d{5})\s*(.*)$", r.replace("\n", " ").strip())
                if mm:
                    plz = mm.group(1)
                    ort = mm.group(2).strip() or None
                    break
    if plz and not ort:
        j = lines.index(plz) if plz in lines else -1
        if j >= 0 and j + 1 < len(lines):
            ort = lines[j + 1]
    _loc_cache[loc_id] = {"id": loc_id, "name": name, "strasse": strasse,
                          "plz": plz, "ort": ort}
    time.sleep(0.4)
    return _loc_cache[loc_id]

DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}")

def parse_group(gid):
    """Gesamtspielplan einer Staffel parsen."""
    html = fetch(f"{BASE}/groupPage",
                 {"displayTyp": "vorrunde", "displayDetail": "meetings",
                  "championship": CHAMP, "group": gid})
    soup = BeautifulSoup(html, "lxml")
    games, cur_date = [], None
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 7:
            continue
        cells = [td.get_text(" ", strip=True) for td in tds]
        # Datum kann leer sein (Fortsetzungszeile) -> letztes merken
        for c in cells[:3]:
            if DATE_RE.match(c):
                cur_date = c
        t = next((c for c in cells[:4] if TIME_RE.match(c)), None)
        loc_id = None
        for td in tds:
            a = td.find("a", href=re.compile(r"courtInfo"))
            if a:
                m = re.search(r"location=(\d+)", a["href"])
                if m:
                    loc_id = m.group(1)
                break
        if not (cur_date and t and loc_id):
            continue
        idx = [i for i, td in enumerate(tds) if td.find("a", href=re.compile(r"courtInfo"))]
        if not idx:
            continue
        p = idx[0]
        try:
            nr, home, away = cells[p+1], cells[p+2], cells[p+3]
        except IndexError:
            continue
        if not home or not away:
            continue
        games.append({"datum": cur_date, "zeit": t[:5], "nr": nr,
                      "heim": home, "gast": away, "loc": loc_id})
    return games

def main():
    hlat, hlon, _ = geo(HOME_PLZ)
    print(f"Basis 21720 Steinkirchen: {hlat:.4f}, {hlon:.4f}", file=sys.stderr)

    out = []
    for gid, (liga, kat, stufe) in GROUPS.items():
        try:
            games = parse_group(gid)
        except Exception as e:
            print(f"  Staffel {gid} fehlgeschlagen: {e}", file=sys.stderr)
            continue
        print(f"  {liga:<22} {len(games):>3} Spiele", file=sys.stderr)
        for g in games:
            h = hall(g["loc"])
            if not h["plz"]:
                continue
            lat, lon, state = geo(h["plz"])
            if math.isnan(lat):
                continue
            dist = haversine(hlat, hlon, lat, lon)
            if dist > RADIUS_KM:
                continue
            # suedlich der Elbe: Schleswig-Holstein raus, HH nur Sued
            if state == "Schleswig-Holstein":
                continue
            if state == "Hamburg" and lat > 53.53:
                continue
            out.append({
                "datum": g["datum"], "zeit": g["zeit"], "nr": g["nr"],
                "liga": liga, "kategorie": kat, "stufe": stufe,
                "heim": g["heim"], "gast": g["gast"],
                "halle": h["name"], "strasse": h.get("strasse"), "plz": h["plz"], "ort": h["ort"],
                "lat": round(lat, 5), "lon": round(lon, 5),
                "entfernung_km": round(dist, 1),
                "quelle": f"{BASE}/groupPage?championship=HVNB+26%2F27&group={gid}",
            })
        time.sleep(0.5)

    for feed in ICS_FEEDS:
        try:
            extra = from_ics(feed)
            out.extend(extra)
            print(f"  {feed['liga']:<22} {len(extra):>3} Heimspiele (ICS)", file=sys.stderr)
        except Exception as e:
            print(f"  ICS {feed.get('liga')} fehlgeschlagen: {e}", file=sys.stderr)

    def key(x):
        d, m, y = x["datum"].split(".")
        return (y, m, d, x["zeit"])
    out.sort(key=key)
    json.dump(out, open(str(__import__("pathlib").Path(__file__).parent / "heimspiele.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"\n{len(out)} Heimspiele im Umkreis gefunden.", file=sys.stderr)

if __name__ == "__main__":
    main()
