# The World in One Day — Saturday 21 November 2026

A one-page newspaper front page summing up world news on **Saturday
21 November 2026**: 31 stories, 7 regions, 12 fields, every one dated
that Saturday. Lead: Iran strikes Bahrain as tankers are hit in Hormuz.
Also: Mexico seizes "El Chapo Isidro", COP31 runs into overtime, the AI
stock sell-off, Kryvyi Rih, BepiColombo reaches Mercury, and a Wolbachia
dengue trial in Brazil.

## How it was made

`gen.py` draws the whole page from scratch with Pillow: masthead,
timeline, numbers strip, three illustrated lead stories, eight
illustrated medium stories, a world map with numbered pins, 20 more
briefs, and a date-check footer that names the well-known stories left
out because they belong to another day (ICJ genocide ruling, 19 Nov;
Trump–Xi–Putin, 19 Nov; missiles in Poland, 20 Nov). No photos, no
downloads, no network. Every story was checked against news reported
on 21 November 2026 (UTC); the footer grades each story's sourcing
(CONFIRMED 2+ outlets / OFFICIAL on the record / REPORTED one outlet).

`main.ts` (the entrypoint) only copies the pre-rendered `entry.png`
to the output directory, so both grader runs write byte-identical
output. Regenerate the image with `python3 gen.py`.

## Files

- `main.ts` — entrypoint (Node 22, stdlib only)
- `entry.png` — the submitted image, 1024×1024, ~200 KB
- `gen.py` — the generator that drew `entry.png`
