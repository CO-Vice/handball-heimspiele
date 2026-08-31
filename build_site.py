#!/usr/bin/env python3
"""
Baut aus heimspiele.json die beiden Dateien, die veröffentlicht werden:
  index.html      – das Dashboard
  heimspiele.ics  – der Kalender zum Abonnieren
"""
import json, hashlib, pathlib
from datetime import datetime, timedelta, timezone

HERE = pathlib.Path(__file__).parent
OUT = HERE / "site"
DUR = 105  # angenommene Spieldauer inkl. Halbzeit, in Minuten


def ics_escape(s):
    return (str(s).replace("\\", "\\\\").replace(",", "\\,")
                  .replace(";", "\\;").replace("\n", "\\n"))


def fold(line):
    """ICS-Zeilen auf 75 Oktette umbrechen, wie es der Standard verlangt."""
    b = line.encode("utf-8")
    if len(b) <= 73:
        return line
    parts, cur = [], b""
    for ch in line:
        e = ch.encode("utf-8")
        if len(cur) + len(e) > 73:
            parts.append(cur.decode("utf-8"))
            cur = b" "
        cur += e
    parts.append(cur.decode("utf-8"))
    return "\r\n".join(parts)


def build_ics(games):
    now = datetime.now(timezone.utc)
    L = ["BEGIN:VCALENDAR", "VERSION:2.0",
         "PRODID:-//Heimspiele Steinkirchen//DE", "CALSCALE:GREGORIAN",
         "METHOD:PUBLISH",
         "X-WR-CALNAME:Handball-Heimspiele Umkreis Steinkirchen",
         "X-WR-TIMEZONE:Europe/Berlin",
         "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
         "X-PUBLISHED-TTL:PT12H"]
    for x in games:
        d, m, y = x["datum"].split(".")
        H, M = x["zeit"].split(":")
        st = datetime(int(y), int(m), int(d), int(H), int(M))
        en = st + timedelta(minutes=DUR)
        uid = hashlib.md5(
            f"{x['datum']}{x['zeit']}{x['heim']}{x['gast']}".encode()).hexdigest()
        loc = f"{x['halle']}, {x.get('strasse') or ''} {x['plz']} {x['ort']}"
        L += ["BEGIN:VEVENT",
              f"UID:{uid}@heimspiele.steinkirchen",
              f"DTSTAMP:{now:%Y%m%dT%H%M%SZ}",
              f"DTSTART;TZID=Europe/Berlin:{st:%Y%m%dT%H%M%S}",
              f"DTEND;TZID=Europe/Berlin:{en:%Y%m%dT%H%M%S}",
              fold(f"SUMMARY:{ics_escape(x['heim'])} – {ics_escape(x['gast'])}"),
              fold(f"LOCATION:{ics_escape(' '.join(loc.split()))}"),
              fold("DESCRIPTION:" + ics_escape(
                  f"{x['liga']} · {x['kategorie']} · "
                  f"{x['entfernung_km']} km ab Steinkirchen")),
              f"GEO:{x['lat']};{x['lon']}",
              "BEGIN:VALARM", "TRIGGER:-PT3H", "ACTION:DISPLAY",
              "DESCRIPTION:Heimspiel heute", "END:VALARM",
              "END:VEVENT"]
    L.append("END:VCALENDAR")
    return "\r\n".join(L) + "\r\n"


def main():
    games = json.loads((HERE / "heimspiele.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)

    slim = [{k: v for k, v in g.items()
             if k not in ("quelle", "nr", "strasse")} for g in games]
    tpl = (HERE / "template.html").read_text(encoding="utf-8")
    (OUT / "index.html").write_text(
        tpl.replace("__DATA__",
                    json.dumps(slim, ensure_ascii=False, separators=(",", ":"))),
        encoding="utf-8")
    (OUT / "heimspiele.ics").write_text(build_ics(games), encoding="utf-8")
    (OUT / "heimspiele.json").write_text(
        json.dumps(games, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"site/ gebaut: {len(games)} Spiele")


if __name__ == "__main__":
    main()
