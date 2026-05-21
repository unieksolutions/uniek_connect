# SHARED_CONTEXT — Template

Gebruik dit template voor multi-agent samenwerking aan een specifiek probleem of taak.
Maak per probleem een nieuw bestand: `SHARED_CONTEXT_{onderwerp}.md`

---

## Doel
{Één zin: wat moet er bereikt worden?}

## Betrokken projecten / agents
| Project | Directory | Verantwoordelijkheid |
|---------|-----------|---------------------|
| {naam} | {/opt/projects/...} | {wat doet deze agent?} |

## Protocol voor elke agent
1. Lees dit bestand volledig vóór je begint
2. Voeg jouw bijdrage toe onder een nieuwe sectie (zie formaat hieronder)
3. Houd je bijdrage beknopt — max 20 regels
4. Geef expliciet aan wat andere agents moeten doen

## Prompt voor vervolgagent
```
Lees /opt/projects/SHARED_CONTEXT_{onderwerp}.md en vul aan:
- Wat heb jij gedaan?
- Wat staat er nog open?
- Wat moeten andere agents doen?
Schrijf dit onder jouw timestamp met naam "{model} working on {project directory}".
```

## Eerste agent — initialisatie prompt
```
Maak op basis van /opt/bootstrap/SHARED_CONTEXT.md een SHARED_CONTEXT_{onderwerp}.md
in /opt/projects/ voor het volgende probleem: {beschrijving}.
Betrokken projecten: {lijst}.
Start daarna met jouw eigen bijdrage.
```

---

## {YYYY-MM-DDTHH:MM} — {model} working on {/opt/projects/naam}

**Gedaan:**
- 

**Open:**
- 

**Voor andere agents:**
- 
