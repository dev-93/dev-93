#!/usr/bin/env python3
"""Combine only the requested local ccusage sources and render the OSS heatmap."""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "node_modules" / ".bin"
SOURCES = ("codex", "antigravity", "claude")
FIELDS = ("inputTokens", "outputTokens", "cacheCreationTokens", "cacheReadTokens")


def main():
    daily = {}
    for source in SOURCES:
        result = subprocess.run([str(BIN / "ccusage"), source, "daily", "--json", "--offline"],
                                cwd=ROOT, capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        if not isinstance(report.get("daily"), list):
            raise ValueError(f"{source}: 일별 데이터 형식이 올바르지 않습니다.")
        for row in report["daily"]:
            day = row["date"]
            total = sum(row.get(field) or 0 for field in FIELDS)
            daily[day] = daily.get(day, 0) + total
        print(f"{source}: {len(report['daily'])}일")

    with tempfile.TemporaryDirectory(prefix="ai-activity-") as temporary:
        tmp = Path(temporary)
        data = tmp / "daily.json"
        data.write_text(json.dumps([{"date": day, "total": total} for day, total in sorted(daily.items())]), encoding="utf-8")
        subprocess.run([str(BIN / "ai-usage-heatmap"), "render", "--source", "json", "--input", str(data), "--out-dir", str(tmp)],
                       cwd=ROOT, check=True)
        for theme in ("light", "dark"):
            name = f"ai-usage-{theme}.svg"
            (ROOT / "assets" / name).write_bytes((tmp / name).read_bytes())


if __name__ == "__main__":
    main()
