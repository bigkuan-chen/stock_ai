from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .config import FRONTEND_DIR
from .pipeline import get_or_create_state, run_analysis


def response_payload(path: str, query: dict[str, list[str]]) -> tuple[int, dict]:
    state = get_or_create_state()
    if path == "/api/health":
        return 200, {"status": "ok", "updated_at": state.get("updated_at")}
    if path == "/api/dashboard":
        return 200, {
            "updated_at": state.get("updated_at"),
            "lookback_days": state.get("lookback_days"),
            "summary": {
                "policies": len(state.get("policies", [])),
                "industries": len(state.get("industries", [])),
                "companies": len(state.get("companies", [])),
            },
            "top_industries": state.get("industries", [])[:5],
            "top_companies": state.get("companies", [])[:8],
            "recent_policies": state.get("policies", [])[:10],
        }
    if path == "/api/policies":
        return 200, {"results": state.get("policies", [])}
    if path == "/api/industries/ranking":
        return 200, {"results": state.get("industries", [])}
    if path == "/api/companies/ranking":
        return 200, {"results": state.get("companies", [])}
    if path == "/api/run-analysis":
        lookback = int(query.get("lookback_days", ["30"])[0])
        offline = query.get("offline", ["false"])[0].lower() == "true"
        return 200, run_analysis(lookback_days=lookback, offline=offline)
    return 404, {"error": "not_found"}


class Handler(BaseHTTPRequestHandler):
    server_version = "PolicyIntelMVP/1.0"

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_POST(self) -> None:
        self.handle_request()

    def do_GET(self) -> None:
        self.handle_request()

    def handle_request(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            status, payload = response_payload(parsed.path, parse_qs(parsed.query))
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.serve_static(parsed.path)

    def serve_static(self, path: str) -> None:
        rel = "index.html" if path in {"/", ""} else path.lstrip("/")
        target = (FRONTEND_DIR / rel).resolve()
        if not str(target).startswith(str(FRONTEND_DIR.resolve())) or not target.exists():
            target = FRONTEND_DIR / "index.html"
        content = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), format % args))


def serve(host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Serving policy intelligence dashboard at http://{host}:{port}/")
    server.serve_forever()
