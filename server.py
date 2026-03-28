import json
import os
import socketserver
import urllib.request
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/contact":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
        if not webhook_url:
            self.send_response(HTTPStatus.SERVICE_UNAVAILABLE)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "ok": False,
                        "error": "DISCORD_WEBHOOK_URL environment variable is not set.",
                    },
                    ensure_ascii=False,
                ).encode("utf-8")
            )
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0

        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            payload = {}

        name = str(payload.get("name") or "").strip()
        phone = str(payload.get("phone") or "").strip()
        email = str(payload.get("email") or "").strip()
        message = str(payload.get("message") or "").strip()

        def clip(value: str, limit: int) -> str:
            v = value.replace("\r\n", "\n").replace("\r", "\n").strip()
            return v[:limit] if len(v) > limit else v

        discord_body = {
            "username": "Lust Medya",
            "embeds": [
                {
                    "title": "Yeni İletişim Formu",
                    "color": 0x6366F1,
                    "fields": [
                        {"name": "Ad Soyad", "value": clip(name or "-", 256), "inline": True},
                        {"name": "Telefon", "value": clip(phone or "-", 256), "inline": True},
                        {"name": "E-Posta", "value": clip(email or "-", 256), "inline": False},
                        {"name": "Mesaj", "value": clip(message or "-", 1800), "inline": False},
                    ],
                }
            ],
        }

        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(discord_body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
        except Exception:
            status = 0

        ok = status in (200, 204)
        self.send_response(HTTPStatus.OK if ok else HTTPStatus.BAD_GATEWAY)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": ok}, ensure_ascii=False).encode("utf-8"))


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port_str = os.environ.get("PORT", "8080")
    port = int(port_str) if port_str.isdigit() else 8080

    with socketserver.TCPServer((host, port), Handler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
