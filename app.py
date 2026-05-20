from flask import Flask, request, jsonify, send_from_directory
import urllib.request
import urllib.parse
import json
import os

app = Flask(__name__, static_folder='public', static_url_path='')

API_BASE = "https://comunicaapi.pje.jus.br"

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/api/v1/comunicacao', methods=['GET', 'OPTIONS'])
def comunicacao():
    if request.method == 'OPTIONS':
        return '', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    
    query = request.query_string.decode('utf-8')
    endpoint = "/api/v1/comunicacao"
    target = f"{API_BASE}{endpoint}?{query}" if query else f"{API_BASE}{endpoint}"
    
    req = urllib.request.Request(
        target,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "identity",
            "Content-Type": "application/json",
            "Referer": "https://www.cnj.jus.br/",
            "Origin": "https://www.cnj.jus.br",
            "X-Forwarded-For": "187.1.1.1",
            "CF-Connecting-IP": "187.1.1.1",
            "CF-IPCountry": "BR",
            "CloudFront-Is-Desktop-Viewer": "true",
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read()
            status_code = resp.status
        
        response = jsonify(json.loads(body))
        response.status_code = status_code
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except urllib.error.HTTPError as e:
        if e.code == 403:
            msg = "Acesso bloqueado pela API PJe (restrição geográfica). Contate o suporte da API."
        else:
            msg = e.read().decode("utf-8", "replace")
        response = jsonify({"error": msg})
        response.status_code = e.code
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        response = jsonify({"error": f"Erro interno: {str(e)}"})
        response.status_code = 500
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
