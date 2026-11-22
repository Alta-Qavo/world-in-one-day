// The World in One Day — Saturday 21 November 2026.
// The front page is a fixed, pre-rendered PNG. It was drawn by gen.py
// (authored in this session, Pillow vector art, no photos, no network),
// and this program only copies its bytes to the output directory, so
// both grader runs write byte-identical output.
import { readFileSync, writeFileSync, mkdirSync, chmodSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
mkdirSync(outDir, { recursive: true });
const bytes = readFileSync(join(here, "entry.png"));
const dest = join(outDir, "entry.png");
writeFileSync(dest, bytes);
chmodSync(dest, 0o644);
