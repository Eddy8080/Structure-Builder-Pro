"""
shield.py — Camada de Sanitização de Dados (Python-side)
Structure Builder Pro | Segurança v1.0

Protege:
  SEC-001 — XSS via innerHTML (nomes de pastas/arquivos)
  SEC-002 — XSS via changelog do GitHub
  SEC-006 — URL de download sem validação de domínio
  SEC-007 — installer_path sem validação
  SEC-011 — Dados sensíveis de sessão (sanitização ao carregar)

Funcionamento:
  Faz monkey-patch em eel._exposed_functions APÓS import bridge,
  envolvendo funções específicas com validações de entrada e
  sanitização de saída. Zero modificações em arquivos existentes.

Chamada em launcher.py:
  import bridge
  from shield import aplicar_shields_eel
  aplicar_shields_eel()
"""

import os
import html as _html_mod
import tempfile
import functools
import eel


# ═══════════════════════════════════════════════════════════════════════════════
# PRIMITIVOS DE SANITIZAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

def _esc(valor):
    """Escapa todos os caracteres HTML perigosos em uma string."""
    if not isinstance(valor, str):
        return valor
    return _html_mod.escape(valor, quote=True)


def _sanitizar_node(node):
    """
    Sanitiza recursivamente os campos de exibição de um nó de árvore.
    Escapa: name, main_folder — preserva campos de controle internos.
    """
    if not isinstance(node, dict):
        return node

    n = dict(node)

    for campo in ('name', 'main_folder'):
        if campo in n and isinstance(n[campo], str):
            n[campo] = _esc(n[campo])

    if 'tree_structure' in n and isinstance(n['tree_structure'], dict):
        n['tree_structure'] = _sanitizar_node(n['tree_structure'])

    if 'children' in n and isinstance(n['children'], list):
        n['children'] = [_sanitizar_node(c) for c in n['children']]

    return n


def _sanitizar_lista_modelos(modelos):
    """Sanitiza uma lista de modelos rápidos (obter_modelos_rapidos)."""
    if not isinstance(modelos, list):
        return modelos
    return [_sanitizar_node(m) for m in modelos]


def _sanitizar_resposta_github(res):
    """
    Sanitiza campos textuais vindos da API do GitHub (SEC-002).
    Escapa: changelog, versões, mensagens informativas.
    Remove assets com URLs não autorizadas (SEC-006 — validação de saída).
    """
    if not isinstance(res, dict):
        return res

    res = dict(res)

    for campo in ('changelog', 'remote_version', 'local_version', 'info', 'message'):
        if campo in res:
            res[campo] = _esc(str(res.get(campo, '')))

    if 'assets' in res and isinstance(res['assets'], list):
        res['assets'] = [
            a for a in res['assets']
            if isinstance(a, dict) and _validar_url_github(
                a.get('browser_download_url', '')
            )
        ]

    return res


def _sanitizar_estado_sessao(data):
    """
    Sanitiza nomes de pastas no estado de sessão ao carregar do disco (SEC-011).
    Protege contra dados corrompidos ou manipulados no mirror_session.json.
    """
    if not isinstance(data, dict):
        return data

    data = dict(data)

    if 'history' in data and isinstance(data['history'], dict):
        historico_limpo = {}
        for path_key, entry in data['history'].items():
            if isinstance(entry, dict) and 'tree' in entry:
                entry = dict(entry)
                entry['tree'] = _sanitizar_node(entry['tree'])
            historico_limpo[path_key] = entry
        data['history'] = historico_limpo

    if 'pinnedSnapshots' in data and isinstance(data['pinnedSnapshots'], dict):
        snaps_limpos = {}
        for path_key, snap in data['pinnedSnapshots'].items():
            if isinstance(snap, dict):
                snap = dict(snap)
                if 'folderName' in snap:
                    snap['folderName'] = _esc(str(snap['folderName']))
                if 'tree' in snap:
                    snap['tree'] = _sanitizar_node(snap['tree'])
            snaps_limpos[path_key] = snap
        data['pinnedSnapshots'] = snaps_limpos

    return data


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDADORES
# ═══════════════════════════════════════════════════════════════════════════════

def _validar_url_github(url):
    """
    Valida que a URL pertence estritamente aos domínios oficiais do GitHub (SEC-006).
    Retorna True apenas para origens confiáveis da plataforma de releases.
    """
    if not isinstance(url, str) or not url.lower().startswith('https://'):
        return False

    DOMINIOS_PERMITIDOS = (
        'https://github.com/',
        'https://api.github.com/',
        'https://objects.githubusercontent.com/',
        'https://github-releases.githubusercontent.com/',
        'https://github-production-release-asset',
        'https://codeload.github.com/',
    )

    return any(url.lower().startswith(d) for d in DOMINIOS_PERMITIDOS)


def _validar_installer_path(path):
    """
    Valida que o caminho do instalador está em %TEMP% e é um .exe (SEC-007).
    Bloqueia: path traversal, null bytes, extensões inesperadas, caminhos externos.
    """
    if not isinstance(path, str) or not path:
        return False

    if '..' in path or '\x00' in path:
        return False

    temp_dir = os.path.normcase(os.path.normpath(tempfile.gettempdir()))
    path_norm = os.path.normcase(os.path.normpath(path))

    if not path_norm.startswith(temp_dir + os.sep):
        return False

    if not path_norm.endswith('.exe'):
        return False

    return True


def validar_caminho_instalador(path):
    """
    API pública do validador de caminho de instalador (SEC-007).
    Usada pelo launcher.py no modo --sidecar-mode, antes do eel estar ativo.
    Mesma lógica de _validar_installer_path — exposta para uso externo ao eel.
    """
    return _validar_installer_path(path)


# ═══════════════════════════════════════════════════════════════════════════════
# MOTOR DE WRAPPING — monkey-patch em eel._exposed_functions
# ═══════════════════════════════════════════════════════════════════════════════

def _criar_wrapper(nome, original):
    """
    Cria um wrapper de segurança para uma função eel exposta.
    Aplica validações de ENTRADA antes e sanitizações de SAÍDA depois.
    """
    @functools.wraps(original)
    def wrapper(*args, **kwargs):

        # ── Validações de ENTRADA ────────────────────────────────────────────

        if nome == 'executar_download_e_atualizar':
            url = args[0] if args else kwargs.get('url_download', '')
            if not _validar_url_github(url):
                print(f"[SHIELD] BLOQUEADO: URL não autorizada → {url!r}")
                return {"error": "URL de download inválida. Apenas releases oficiais do GitHub são permitidos."}

        elif nome == 'finalizar_e_instalar':
            path = args[0] if args else kwargs.get('installer_path', '')
            if not _validar_installer_path(path):
                print(f"[SHIELD] BLOQUEADO: Caminho de instalador inválido → {path!r}")
                return {"error": "Caminho do instalador inválido. Deve ser um .exe dentro de %TEMP%."}

        # ── Executa a função original ────────────────────────────────────────

        resultado = original(*args, **kwargs)

        # ── Sanitizações de SAÍDA ────────────────────────────────────────────

        if nome == 'verificar_atualizacao_disponivel':
            resultado = _sanitizar_resposta_github(resultado)

        elif nome == 'obter_modelos_rapidos':
            resultado = _sanitizar_lista_modelos(resultado)

        elif nome in (
            'carregar_estrutura_existente',
            'adicionar_modelo_rapido',
            'sincronizar_no_windows',
            'aplicar_espelhamento',
        ):
            if isinstance(resultado, dict):
                resultado = _sanitizar_node(resultado)

        elif nome == 'carregar_estado_espelhamento':
            resultado = _sanitizar_estado_sessao(resultado)

        return resultado

    return wrapper


# ═══════════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA PÚBLICO
# ═══════════════════════════════════════════════════════════════════════════════

# Funções que receberão wrapping de segurança
_FUNCOES_PROTEGIDAS = {
    # Validação de entrada
    'executar_download_e_atualizar',
    'finalizar_e_instalar',
    # Sanitização de saída
    'verificar_atualizacao_disponivel',
    'carregar_estrutura_existente',
    'obter_modelos_rapidos',
    'adicionar_modelo_rapido',
    'sincronizar_no_windows',
    'aplicar_espelhamento',
    'carregar_estado_espelhamento',
}


def aplicar_shields_eel():
    """
    Aplica wrapping de segurança sobre as funções eel expostas.
    Deve ser chamado APÓS 'import bridge' (quando _exposed_functions está populado)
    e ANTES de bridge.iniciar_app().
    """
    total = len(_FUNCOES_PROTEGIDAS)
    aplicadas = 0

    for nome in _FUNCOES_PROTEGIDAS:
        if nome in eel._exposed_functions:
            original = eel._exposed_functions[nome]
            eel._exposed_functions[nome] = _criar_wrapper(nome, original)
            aplicadas += 1
        else:
            print(f"[SHIELD] Aviso: '{nome}' não encontrada em _exposed_functions.")

    print(f"[SHIELD] {aplicadas}/{total} funções protegidas com sucesso.")
