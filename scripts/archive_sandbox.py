from __future__ import annotations

import datetime
import pathlib
import shutil

root = pathlib.Path(__file__).resolve().parents[1]
stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
arch_dir = root / "_archive"
arch_dir.mkdir(exist_ok=True)

# ensure targets exist
targets = [root / "scratch", root / "artifacts", root / "reports"]
for t in targets:
    t.mkdir(parents=True, exist_ok=True)

bundle = arch_dir / f"sandbox_{stamp}"
shutil.make_archive(str(bundle), "zip", root_dir=root, base_dir="scratch")
shutil.make_archive(
    str(bundle) + "_artifacts", "zip", root_dir=root, base_dir="artifacts"
)
shutil.make_archive(str(bundle) + "_reports", "zip", root_dir=root, base_dir="reports")

for t in targets:
    shutil.rmtree(t, ignore_errors=True)
print(f"Archived → {bundle}.zip (+ _artifacts.zip, _reports.zip)")
