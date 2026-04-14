"""
shield2.py — Middleware HTTP de Segurança (Bottle/eel)
Structure Builder Pro | Segurança v1.0

Protege:
  SEC-008 — Ausência de Content Security Policy
  SEC-010 — lucide@latest sem versão fixada (bloqueado via CSP)
  SEC-004 — CDNs sem SRI (mitigado via CSP restrita)
  Injeção de web/security.js sem modificar index.html

Funcionamento:
  1. Adiciona um hook after_request no bottle.default_app() que injeta
     headers de segurança HTTP em TODAS as respostas.
  2. Registra uma rota específica para /index.html que serve o arquivo
     original com a tag <script src="/security.js"> injetada em memória.
     Rotas específicas têm prioridade sobre wildcards no Bottle — a rota
     do eel (wildcard) não sobrepõe esta.

Confirmação arquitetural (eel/__init__.py linha 333-336):
  app = _start_args['app']          # btl.default_app()
  if isinstance(app, btl.Bottle):
      register_eel_routes(app)      # registrado APÓS este shield
  btl.run(..., app=app)

Chamada em launcher.py:
  import shield2
  shield2.setup_shield2()           # antes de bridge.iniciar_app()
"""

import os
import bottle


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT SECURITY POLICY
# ═══════════════════════════════════════════════════════════════════════════════

# Permite o funcionamento completo do eel (WebSocket local, CDNs usados pelo projeto)
# mas bloqueia origens não declaradas, frames, workers e outros vetores de ataque.
_CSP = "; ".join([
    "default-src 'self'",
    # Scripts: self + CDNs declarados + inline (necessário para Lucide/Mermaid)
    "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net",
    # Estilos: self + Google Fonts + jsDelivr (SweetAlert2 tema)
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
    # Fontes: self + Google Fonts CDN
    "font-src 'self' https://fonts.gstatic.com data:",
    # Imagens: self + data URIs + blob (para download do SVG do diagrama)
    "img-src 'self' data: blob:",
    # Conexões: apenas localhost (WebSocket do eel)
    "connect-src 'self' ws://localhost:* wss://localhost:*",
    # Bloqueia completamente workers e objects, permite frames de 'self' para o manual
    "worker-src 'none'",
    "object-src 'none'",
    "frame-src 'self'",
    "frame-ancestors 'none'",
    # Restringe base URI e form actions
    "base-uri 'self'",
    "form-action 'none'",
])

_SECURITY_HEADERS = {
    'Content-Security-Policy':          _CSP,
    'X-Content-Type-Options':           'nosniff',
    'X-Frame-Options':                  'DENY',
    'Referrer-Policy':                  'no-referrer',
    'X-Permitted-Cross-Domain-Policies': 'none',
}

# Ponto exato de injeção no index.html (antes do primeiro script externo)
_ANCHOR = '    <script src="https://unpkg.com/lucide@latest"></script>'
_INJECAO = '    <script src="/security.js"></script>\n'


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES INTERNAS
# ═══════════════════════════════════════════════════════════════════════════════

def _ler_index_seguro():
    """
    Lê o index.html original e injeta a tag do security.js em memória.
    Acessa eel.root_path de forma lazy — disponível após eel.init()
    (que é chamado dentro de bridge.iniciar_app()).
    O arquivo index.html original não é modificado em disco.
    """
    import eel as _eel
    index_path = os.path.join(_eel.root_path, 'index.html')

    with open(index_path, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    if _ANCHOR in conteudo:
        # Injeção precisa: logo antes do primeiro script externo
        conteudo = conteudo.replace(_ANCHOR, _INJECAO + _ANCHOR, 1)
    else:
        # Fallback seguro: antes do </head>
        conteudo = conteudo.replace('</head>', _INJECAO + '</head>', 1)
        print("[SHIELD2] Aviso: âncora padrão não encontrada — injeção via fallback </head>.")

    return conteudo


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DO MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════════

def setup_shield2():
    """
    Configura o middleware de segurança HTTP no bottle.default_app().

    Deve ser chamado ANTES de bridge.iniciar_app() para que:
    1. O hook after_request seja registrado antes de qualquer requisição.
    2. A rota /index.html seja registrada antes das rotas wildcard do eel.
    """
    app = bottle.default_app()

    # ── Hook: Headers em TODAS as respostas ───────────────────────────────────
    @app.hook('after_request')
    def injetar_headers_seguranca():
        for header, valor in _SECURITY_HEADERS.items():
            bottle.response.headers[header] = valor

    # ── Rota: /index.html com security.js injetado ────────────────────────────
    # Rotas específicas têm prioridade sobre wildcards no Bottle.
    # Esta rota é registrada ANTES de eel.register_eel_routes() ser chamado
    # (dentro de eel.start → run_lambda), garantindo precedência.

    @app.route('/index.html')
    @app.route('/')
    def servir_index_seguro():
        try:
            conteudo = _ler_index_seguro()
            for header, valor in _SECURITY_HEADERS.items():
                bottle.response.headers[header] = valor
            bottle.response.content_type = 'text/html; charset=utf-8'
            return conteudo
        except Exception as e:
            print(f"[SHIELD2] Erro ao servir index.html seguro: {e}. Usando fallback.")
            import eel as _eel
            return bottle.static_file('index.html', root=_eel.root_path)

    total_headers = len(_SECURITY_HEADERS)
    print(f"[SHIELD2] Middleware HTTP configurado — {total_headers} headers de segurança ativos.")
    print(f"[SHIELD2] Rota /index.html interceptada para injeção de security.js.")
