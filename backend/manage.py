from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.api import serve
from app.config import DEFAULT_LOOKBACK_DAYS
from app.pipeline import run_analysis
from app.storage import DATA_FILE


def main() -> None:
    parser = argparse.ArgumentParser(description="Policy intelligence MVP")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="crawl and calculate policy opportunity scores")
    analyze.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    analyze.add_argument("--offline", action="store_true", help="use bundled samples instead of live crawling")

    server = sub.add_parser("serve", help="start local API and dashboard server")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    if args.command == "analyze":
        result = run_analysis(lookback_days=args.lookback_days, offline=args.offline)
        print(json.dumps({
            "status": "ok",
            "policies": len(result["policies"]),
            "industries": len(result["industries"]),
            "companies": len(result["companies"]),
            "data_file": str(Path(DATA_FILE).resolve()),
        }, ensure_ascii=False, indent=2))
        return

    if args.command == "serve":
        serve(args.host, args.port)


if __name__ == "__main__":
    main()
