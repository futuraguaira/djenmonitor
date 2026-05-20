"""
Vercel Serverless Function — Proxy para API Comunica PJe
=========================================================
Rota:  /api/v1/comunicacao
Método: GET

Recebe os query params do painel (numeroOab, ufOab, page, size, datas...),
repassa para comunicaapi.pje.jus.br e devolve o JSON ao browser.
Resolve o bloqueio de CORS: a chamada real sai do servidor da Vercel,
não do browser do usuário.
"""

from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json

API_BASE = "https://comunicaapi.pje.jus.br"


class handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # silencia logs verbose da Vercel

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        # Monta URL completa para a API PJe
        parsed   = urllib.parse.urlparse(self.path)
        query    = parsed.query
        endpoint = "/api/v1/comunicacao"
        target   = f"{API_BASE}{endpoint}?{query}" if query else f"{API_BASE}{endpoint}"

        req = urllib.request.Request(
            target,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Content-Type": "application/json",
                "Referer": "https://www.cnj.jus.br/",
                "Origin": "https://www.cnj.jus.br",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site",
                "X-Forwarded-For": "187.1.1.1",
                "CF-Connecting-IP": "187.1.1.1",
                "CF-IPCountry": "BR",
                "CloudFront-Is-Desktop-Viewer": "true",
                "CloudFront-Is-Mobile-Viewer": "false",
                "Cache-Control": "no-cache",
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                body        = resp.read()
                status_code = resp.status

            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        except urllib.error.HTTPError as e:
            body = e.read()
            # Trata 403 como bloqueio geográfico
            if e.code == 403:
                msg = "Acesso bloqueado pela API PJe (restrição geográfica). Contate o suporte da API."
            else:
                msg = body.decode("utf-8", "replace")
            self._send_error(e.code, msg)

        except urllib.error.URLError as e:
            self._send_error(502, f"Erro ao acessar a API PJe: {e.reason}")

        except Exception as e:
            self._send_error(500, f"Erro interno: {str(e)}")

    def _send_error(self, code, message):
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(body)
