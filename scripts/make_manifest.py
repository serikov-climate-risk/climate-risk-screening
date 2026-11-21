"""Write data/manifest.csv with SHA-256 checksums and sizes of every raw data file."""
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
rows = ["path,bytes,sha256"]
for p in sorted((root / "data" / "raw").rglob("*")):
    if p.is_file() and p.suffix in {".tif", ".json", ".zip", ".txt", ".geojson"} and "log" not in p.name:
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        rows.append(f"{p.relative_to(root).as_posix()},{p.stat().st_size},{h}")
(root / "data" / "manifest.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
print(len(rows) - 1, "files")
