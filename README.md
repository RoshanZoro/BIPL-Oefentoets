# BIPL Toets Oefening

Een desktop-oefenprogramma voor de theorie van het **BIPL**-vak (Netwerken & Platformen, weken 1–7). Gebouwd met Python en Tkinter — geen externe packages nodig.

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-lightgrey)
![Vragen](https://img.shields.io/badge/Vragen-411-green)
![Licentie](https://img.shields.io/badge/Licentie-MIT-yellow)

---

## Functies

- **411 vragen** over alle stof van weken 1 t/m 7
- **20 willekeurige vragen** per sessie uit de vragenbank
- Antwoordopties worden **elke keer opnieuw geschud** — geen vaste posities onthouden
- **Directe feedback** — juist antwoord groen, fout antwoord rood met het correcte antwoord zichtbaar
- **Scoreoverzicht** aan het einde met alle fout beantwoorde vragen en de correcte antwoorden
- Meteen **opnieuw spelen** of terug naar het hoofdmenu
- **Dynamisch menu** — voeg een nieuw JSON-bestand toe aan de `questions/`-map en er verschijnt automatisch een nieuwe knop

---

## Onderwerpen

| Onderwerp | Vragen |
|---|---|
| Netwerken – Week 1 (OSI-model, Cisco IOS, CLI, LAN/WAN, lab, beveiliging) | 56 |
| Netwerken – Week 2 (IPv4, subnetting, VLSM, Ethernet, ARP, kabels, fysieke laag) | 107 |
| Netwerken – Week 3 (VLANs, trunking, DTP, switching, RIP, IPv6, inter-VLAN routing) | 80 |
| Netwerken – Week 4 (SSH, router-on-a-stick, L3-switch, simpel netwerk opdracht) | 30 |
| Netwerken – Week 5 (DHCP, transportlaag, TCP/UDP, troubleshooting, OSI lagen 5–7) | 56 |
| Netwerken – Week 6 (TCP three-way handshake, UDP, DNS, SMTP, FTP, Wireshark) | 39 |
| Netwerken – Week 7 (CDP, LLDP, show version, verificatie) | 18 |
| Netwerken – Algemeen (CLI, interfaces, configuratiebeheer, verificatie) | 25 |
| **Totaal** | **411** |

---

## Vereisten

- Python 3.x
- Tkinter (standaard meegeleverd met Python)

Geen `pip install` nodig.

> **Alleen Linux:** Als Tkinter ontbreekt, installeer het met:
> ```bash
> sudo apt install python3-tk        # Debian / Ubuntu
> sudo dnf install python3-tkinter   # Rocky Linux / RHEL / Fedora
> ```

---

## Gebruik

```bash
python3 bipl_quiz.py
```

---

## Projectstructuur

```
bipl_quiz.py
questions/
    Netwerken-en-Platformen-Week-1-2-3-4.json
README.md
```

De vragen staan **niet** meer in `bipl_quiz.py` zelf, maar in afzonderlijke JSON-bestanden in de `questions/`-map. Het programma scant deze map automatisch bij het opstarten en maakt voor elk bestand een knop in het hoofdmenu.

---

## Vragensets toevoegen of uitbreiden

### Nieuw JSON-bestand toevoegen

Maak een nieuw `.json`-bestand aan in de `questions/`-map. De bestandsnaam bepaalt automatisch de tekst op de knop:

| Bestandsnaam | Knoptekst |
|---|---|
| `Netwerken-en-Platformen-Week-1-2-3-4.json` | Netwerken en Platformen Week 1 t/m 4 |
| `Netwerken-en-Platformen-Week-1-7.json` | Netwerken en Platformen Week 1 t/m 7 |
| `Linux-Basics.json` | Linux Basics |

Herstart het programma — de nieuwe knop verschijnt vanzelf.

### JSON-formaat

Elk JSON-bestand is een lijst van vraagobjecten:

```json
[
  {
    "question": "Welk commando toont de routing-tabel op Cisco IOS?",
    "options": ["show interfaces", "show ip route", "show arp", "show version"],
    "correct": 1,
    "topic": "Netwerken – Week 1"
  }
]
```

| Veld | Type | Beschrijving |
|---|---|---|
| `question` | string | De vraagtekst |
| `options` | lijst van 4 strings | De antwoordopties |
| `correct` | getal (0–3) | Index van het juiste antwoord (0 = eerste optie) |
| `topic` | string | Onderwerplabel dat in de quiz wordt getoond |

> **Let op:** `correct` verwijst naar de **originele, ongeschudde** volgorde in `options`. De app schudt de opties automatisch bij elke vraag.
