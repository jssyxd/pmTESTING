#!/usr/bin/env python3
"""Step-0 Polymarket weather-events snapshot fetcher (anti-hallucination).

Fetches the Polymarket public events API, filters temperature weather events,
and saves the raw response plus the five-field sidecar meta
(url/status/fetched_at_utc/bytes/sha256) so city documents can quote event
URLs, settlement dates and market types verbatim from disk.

On any failure the script exits non-zero and writes nothing but the error
evidence file; callers must then write null event rows + reason in the docs.
Event URLs must never be hand-filled from memory.
"""

import argparse
import hashlib
import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_URL = "https://gamma-api.polymarket.com/events?"
DEFAULT_PARAMS = {
    "closed": "false",
    "limit": "100",
    "order": "volume24hr",
    "ascending": "false",
}
READ_TIMEOUT = 30
CONNECT_TIMEOUT = 10
MAX_ATTEMPTS = 3
BACKOFF = (2, 5, 10)


def fetch(url: str) -> tuple[int | None, bytes, list]:
    attempts = []
    last_err = None
    for i in range(MAX_ATTEMPTS):
        ts = datetime.now(timezone.utc).isoformat()
        try:
            req = Request(url, headers={"User-Agent": "poly-weather-data-skill/2.0",
                                        "Accept": "application/json"})
            with urlopen(req, timeout=READ_TIMEOUT) as resp:  # nosec B310: fixed trusted Polymarket host
                body = resp.read()
                attempts.append({"ts": ts, "status": resp.status, "bytes": len(body)})
                return resp.status, body, attempts
        except HTTPError as exc:  # noqa: PERF203
            body = exc.read()
            attempts.append({"ts": ts, "status": exc.code, "bytes": len(body),
                             "error": body.decode("utf-8", errors="replace")[:200]})
            if exc.code in (404, 400):
                return exc.code, body, attempts
            last_err = exc
        except (URLError, TimeoutError, OSError, socket.timeout) as exc:
            attempts.append({"ts": ts, "status": None, "error": f"{type(exc).__name__}: {exc}"})
            last_err = exc
        if i < MAX_ATTEMPTS - 1:
            time.sleep(BACKOFF[i])
    raise last_err  # type: ignore[misc]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL + urlencode(DEFAULT_PARAMS))
    ap.add_argument("--out-dir", required=True, help="city evidence dir (raw/ subdir used)")
    ap.add_argument("--city-filter", default="",
                    help="optional comma-separated city names to report counts for")
    args = ap.parse_args()

    out_dir = Path(args.out_dir) / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    status, body, attempts = fetch(args.url)
    now = datetime.now(timezone.utc).isoformat()
    raw_path = out_dir / "polymarket_snapshot.json"
    raw_path.write_bytes(body)
    (out_dir / "polymarket_snapshot.json.meta.json").write_text(json.dumps({
        "url": args.url, "status": status, "fetched_at_utc": now,
        "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
        "attempts": attempts,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    if status != 200:
        print(f"SNAPSHOT_FAIL status={status} bytes={len(body)} attempts={len(attempts)}", flush=True)
        raise SystemExit(1)
    try:
        events = json.loads(body.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"SNAPSHOT_FAIL invalid json: {exc}", flush=True)
        raise SystemExit(1)
    items = events if isinstance(events, list) else events.get("events") or []
    weather = [e for e in items if "weather" in str(e.get("slug", "")).lower()
               or "temperature" in str(e.get("title", "")).lower()]
    print(f"SNAPSHOT_OK total={len(items)} weather_candidates={len(weather)} "
          f"fetched_at={now}", flush=True)
    for city in [c.strip() for c in args.city_filter.split(",") if c.strip()]:
        hits = [e for e in weather if city in str(e.get("title", ""))]
        print(f"  city={city} events={len(hits)}", flush=True)


if __name__ == "__main__":
    main()
