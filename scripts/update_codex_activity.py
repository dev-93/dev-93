#!/usr/bin/env python3
"""Render the signed-in Codex account's daily token activity as an SVG."""
import datetime as dt
import html
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "assets" / "codex-activity.svg"


def read_usage():
    process = subprocess.Popen([os.environ.get("CODEX_BIN", "codex"), "app-server"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True)
    def request(message, request_id):
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()
        for line in process.stdout:
            reply = json.loads(line)
            if reply.get("id") == request_id:
                if "error" in reply:
                    raise RuntimeError("Codex 사용량 조회에 실패했습니다.")
                return reply.get("result") or {}
        raise RuntimeError("Codex 앱 서버가 응답하지 않았습니다.")
    try:
        request({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "profile_activity", "version": "1.0.0"}}}, 1)
        process.stdin.write('{"method":"initialized"}\n')
        process.stdin.flush()
        return request({"id": 2, "method": "account/usage/read"}, 2)
    finally:
        process.terminate()
        process.wait(timeout=5)


def render(usage):
    buckets = usage.get("dailyUsageBuckets")
    if not isinstance(buckets, list):
        raise ValueError("일별 활동 데이터가 없습니다.")
    totals = {}
    for entry in buckets:
        day, tokens = entry.get("startDate"), entry.get("tokens")
        if isinstance(day, str) and isinstance(tokens, int) and tokens >= 0:
            dt.date.fromisoformat(day)
            totals[day] = totals.get(day, 0) + tokens
    today = dt.datetime.now(dt.timezone.utc).date()
    last_sunday = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    first = last_sunday - dt.timedelta(weeks=51)
    colors = ["#ebedf0", "#fed7aa", "#fb923c", "#ea580c", "#9a3412"]
    maximum = max(totals.values(), default=0)
    pieces = ['<svg xmlns="http://www.w3.org/2000/svg" width="690" height="150" viewBox="0 0 690 150" role="img" aria-label="Codex 일별 토큰 활동">', '<rect width="690" height="150" rx="8" fill="#ffffff"/>', '<text x="12" y="22" font-family="sans-serif" font-size="14" fill="#24292f">Codex 일별 토큰 활동</text>']
    for week in range(52):
        for day in range(7):
            date = first + dt.timedelta(days=week * 7 + day)
            if date > today:
                continue
            amount = totals.get(date.isoformat(), 0)
            level = 0 if not amount or not maximum else min(4, 1 + (amount * 4 - 1) // maximum)
            pieces.append(f'<rect x="{12 + week * 13}" y="{32 + day * 13}" width="10" height="10" rx="2" fill="{colors[level]}"><title>{html.escape(date.isoformat())}: {amount:,} tokens</title></rect>')
    pieces.append(f'<text x="12" y="140" font-family="sans-serif" font-size="11" fill="#57606a">기준: {today.isoformat()} UTC · 색이 진할수록 일일 토큰 사용량이 많음</text></svg>\n')
    return "".join(pieces)


def main():
    svg = render(read_usage())
    DESTINATION.parent.mkdir(exist_ok=True)
    DESTINATION.write_text(svg, encoding="utf-8")
    print("Codex 활동 그래프를 갱신했습니다.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
