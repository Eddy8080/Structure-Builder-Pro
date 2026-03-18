"""
launcher.py — Ponto de Entrada Seguro
Structure Builder Pro | Segurança v1.0

Substitui a execução direta de bridge.py adicionando as camadas de segurança
ANTES de iniciar o aplicativo, sem modificar nenhum arquivo homologado.

Arquivos existentes (intocáveis):
  bridge.py, folder_engine.py, web/index.html, web/script.js, web/style.css

Arquivos novos (camada de segurança):
  launcher.py   — este arquivo (ponto de entrada)
  shield.py     — sanitização de dados Python / validação de entradas eel
  shield2.py    — middleware HTTP Bottle / injeção de security.js
  web/security.js — patches de runtime JavaScript

Cobertura de segurança:
  SEC-001 ✓ shield.py   — XSS via innerHTML (nomes sanitizados antes de chegar ao JS)
  SEC-002 ✓ shield.py   — XSS via changelog GitHub
  SEC-003 ✓ security.js — Injeção em onclick (trap de propriedade no window)
  SEC-004 ✓ shield2.py  — CDNs sem SRI (mitigado via CSP)
  SEC-005 ✓ security.js — mermaid securityLevel: loose bloqueado
  SEC-006 ✓ shield.py   — URL de download validada (somente GitHub oficial)
  SEC-007 ✓ shield.py   — installer_path validado (%TEMP% + .exe)
  SEC-008 ✓ shield2.py  — Content Security Policy + 5 headers de segurança HTTP
  SEC-009 ✓ security.js — Proteção das funções globais window.*
  SEC-010 ✓ shield2.py  — CSP restringe carregamento não autorizado de scripts
  SEC-011 ✓ shield.py   — Sanitização do estado de sessão ao carregar do disco

Uso em desenvolvimento:
  python launcher.py

Para compilação com PyInstaller (substitui bridge.py como entry point):
  pyinstaller --name StructureBuilderPro --onefile launcher.py [demais flags]

Nota: O modo --sidecar-mode é delegado diretamente ao bridge.py,
pois não usa a interface web e não requer os shields HTTP.
"""

import sys


def main():
    # ── Modo Sidecar (atualização silenciosa) ─────────────────────────────────
    # QA-001 — SEC-007: valida o caminho do instalador ANTES de delegar ao bridge.py.
    # shield.py é importado diretamente aqui pois o eel ainda não está ativo.
    # bridge.py permanece intocado — o escudo é aplicado na fronteira de entrada.
    if len(sys.argv) >= 3 and sys.argv[1] == '--sidecar-mode':
        installer_path = sys.argv[2]

        from shield import validar_caminho_instalador
        if not validar_caminho_instalador(installer_path):
            print(f"[SHIELD] BLOQUEADO: caminho de instalador inválido no modo sidecar → {installer_path!r}")
            print("[SHIELD] O instalador deve ser um .exe localizado em %TEMP%.")
            sys.exit(1)

        import bridge
        bridge.executar_logica_sidecar(installer_path)
        return

    # ── Modo Normal ───────────────────────────────────────────────────────────

    # Passo 1: Importa bridge.py
    # Executa o código de módulo (os.chdir, ctypes, signal, engine, version_manager)
    # e registra todas as funções @eel.expose em eel._exposed_functions.
    import bridge  # noqa: F401  (importado pelo efeito colateral de registro)

    # Passo 2: Aplica shield de dados (Python-side)
    # Faz monkey-patch em eel._exposed_functions com wrappers de validação
    # e sanitização. Deve ocorrer após import bridge (funções já registradas)
    # e antes de bridge.iniciar_app() (que inicia o servidor).
    from shield import aplicar_shields_eel
    aplicar_shields_eel()

    # Passo 3: Configura middleware HTTP (Bottle-side)
    # Adiciona hook after_request (headers de segurança) e rota /index.html
    # (injeção de security.js em memória) ao bottle.default_app().
    # Deve ocorrer antes de bridge.iniciar_app() → eel.start() →
    # register_eel_routes() para garantir precedência da rota específica.
    import shield2
    shield2.setup_shield2()

    # Passo 4: Inicia o aplicativo normalmente
    # bridge.iniciar_app() chama eel.init() e depois eel.start(),
    # que registra as rotas wildcard do eel APÓS as do shield2.
    try:
        bridge.iniciar_app()
    except KeyboardInterrupt:
        bridge.fechar_aplicacao(None, None)


if __name__ == '__main__':
    main()
