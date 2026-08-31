# Handball-Heimspiele im Umkreis Steinkirchen

Sammelt die Heimspiele hochklassiger Handballmannschaften im Umkreis von 30 km
um 21720 Steinkirchen, südlich der Elbe, und veröffentlicht sie als Webseite
und als Kalender zum Abonnieren.

Erfasst werden aktuell:

| Ebene | Wettbewerb | Quelle |
|---|---|---|
| 3. Liga | Nord-West (VfL Fredenbeck) | Vereinsseite |
| Regionalliga | Männer, mJA, mJB | nuLiga HVNB |
| Oberliga | Männer, mJA, mJB | nuLiga HVNB |
| Jugendbundesliga | 2. JBLH mA Nord, JBLH mB (VfL Horneburg) | **noch offen** |

Die Jugendbundesliga betreut der DHB selbst. Die Termine für 26/27 sind wegen
der Umstellung auf Handball360 noch nicht öffentlich. `watch_jblh.py` meldet
sich, sobald sie auftauchen.

## Einrichten

1. Repo auf GitHub anlegen und diesen Inhalt hineinschieben.
2. Der Workflow schaltet GitHub Pages beim ersten Lauf selbst frei.
3. Unter Actions einmal „Heimspiele aktualisieren“ manuell starten.

Danach läuft es täglich um 05:12 UTC von allein. Ergebnis:

- Dashboard: `https://<name>.github.io/<repo>/`
- Kalender:  `https://<name>.github.io/<repo>/heimspiele.ics`
- Rohdaten:  `https://<name>.github.io/<repo>/heimspiele.json`

## Kalender abonnieren

In Google Calendar links bei „Weitere Kalender“ auf **+** → **Per URL** und
die `.ics`-Adresse eintragen. Wichtig: Google holt abonnierte Kalender in
eigenem Rhythmus, oft nur alle 12 bis 24 Stunden, gelegentlich seltener. Für
den Spielplan einer ganzen Saison reicht das gut; wer Verlegungen am selben
Tag sehen will, schaut besser ins Dashboard.

Zum Weitergeben genügt derselbe Link. Wer ihn abonniert, bekommt die Spiele in
seinen eigenen Kalender, ohne Konto und ohne Freigabe.

## Anpassen

**Radius und Startpunkt** stehen oben in `collect_heimspiele.py`
(`HOME_PLZ`, `RADIUS_KM`).

**Weitere Staffeln** werden in `GROUPS` eingetragen. Die IDs stehen im
Ligenplan des HVNB:
`https://hvnb-handball.liga.nu/cgi-bin/WebObjects/nuLigaHBDE.woa/wa/leaguePage?championship=HVNB+26%2F27`
Jeder Staffel-Link endet auf `&group=NNNNNN`, das ist die ID. Frauen und
weibliche Jugend sind bewusst nicht aktiviert; dafür einfach die
entsprechenden Gruppen ergänzen.

**Wettbewerbe oberhalb des Landesverbands** (3. Liga, Jugendbundesliga) stehen
nicht in nuLiga. Wenn es dafür einen ICS-Feed gibt, kommt er in `ICS_FEEDS`.

**Saisonwechsel:** in `collect_heimspiele.py` `CHAMP` auf die neue Saison
setzen und die Gruppen-IDs neu heraussuchen — die ändern sich jedes Jahr.

## Dateien

    collect_heimspiele.py   sammelt und filtert die Spiele -> heimspiele.json
    build_site.py           baut daraus site/index.html und site/heimspiele.ics
    watch_jblh.py           prüft, ob die Jugendbundesliga-Termine da sind
    template.html           Vorlage für das Dashboard
    .github/workflows/      täglicher Lauf und Veröffentlichung

## Verlässlichkeit

Die Anwurfzeiten stammen aus nuLiga und ändern sich dort auch kurzfristig.
Der tägliche Lauf holt jede Änderung mit, aber zwischen einer Verlegung und
dem nächsten Lauf liegen bis zu 24 Stunden. Vor der Fahrt lohnt der Blick auf
die Staffelseite; sie ist in `heimspiele.json` pro Spiel unter `quelle`
verlinkt.
