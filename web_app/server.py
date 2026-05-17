"""Standard-library Web Interface adapter for the Marketing Agent."""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from src.marketing_agent import MarketingAgent, UserIntervention


ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT_DIR / "web" / "static"


class MarketingAgentRequestHandler(BaseHTTPRequestHandler):
    """HTTP adapter that delegates domain work to MarketingAgent."""

    server_version = "ContentAgent/0.1"

    def do_GET(self) -> None:
        if self.path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return

        if self.path in {"/", "/index.html"}:
            self._serve_static_file(STATIC_DIR / "index.html")
            return

        requested = (STATIC_DIR / self.path.lstrip("/")).resolve()
        if STATIC_DIR not in requested.parents or not requested.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        self._serve_static_file(requested)

    def do_POST(self) -> None:
        if self.path != "/api/marketing-plan":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        try:
            payload = self._read_json_body()
            source = payload.get("software_source", "")
            interventions = _parse_interventions(payload.get("user_interventions", []))
            plan = self.server.marketing_agent.generate_marketing_plan(source, interventions)  # type: ignore[attr-defined]
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Request body must be valid JSON."})
            return
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        self._send_json(HTTPStatus.OK, {"marketing_plan": plan.to_dict()})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(content_length).decode("utf-8")
        payload = json.loads(body or "{}")
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def _serve_static_file(self, path: Path) -> None:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        content = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


class MarketingAgentHTTPServer(ThreadingHTTPServer):
    """HTTP server with an injected MarketingAgent."""

    def __init__(self, server_address: tuple[str, int], marketing_agent: MarketingAgent | None = None):
        super().__init__(server_address, MarketingAgentRequestHandler)
        self.marketing_agent = marketing_agent or MarketingAgent()


def _parse_interventions(raw_items: object) -> tuple[UserIntervention, ...]:
    if raw_items is None:
        return ()
    if not isinstance(raw_items, list):
        raise ValueError("user_interventions must be a list.")

    interventions: list[UserIntervention] = []
    for item in raw_items:
        if not isinstance(item, dict):
            raise ValueError("Each UserIntervention must be an object.")
        interventions.append(
            UserIntervention(
                stage_name=str(item.get("stage_name", "")),
                feedback=str(item.get("feedback", "")),
            )
        )
    return tuple(interventions)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    httpd = MarketingAgentHTTPServer((host, port))
    print(f"ContentAgent Web Interface running at http://{host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
