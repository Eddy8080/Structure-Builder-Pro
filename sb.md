## Structure Builder Pro v5.6.2 — Visão Geral

**Propósito:** Aplicação desktop Windows da Anagma para criar, editar e espelhar hierarquias de pastas, com interface Chromium renderizada via Python+Eel.

---

### Arquitetura em camadas

```
launcher.py          ← Ponto de entrada (substitui bridge.py como entrypoint no build)
   ├── shield.py     ← Sanitização Python-side (monkey-patch nas funções eel)
   ├── shield2.py    ← Middleware HTTP Bottle (CSP headers + injeção de security.js)
   └── bridge.py     ← Registra @eel.expose + inicia janela Chromium
        ├── folder_engine.py   ← Motor de arquivos (scan, criação, espelhamento)
        ├── version_control.py ← Updater via GitHub Releases API
        └── window_manager.py  ← Fixa ícone/AppUserModelID na janela Chromium

web/
   ├── index.html    ← UI: sidebar + painel principal + painel de espelhamento
   ├── script.js     ← Toda lógica client-side (árvore virtual, drag, snapshots)
   ├── style.css     ← Tema dark/light, glassmorphism
   └── security.js   ← Shields runtime JS (injetado pelo shield2.py em memória)
```

---

### Módulos principais

| Arquivo | Responsabilidade |
|---|---|
| `launcher.py` | Sequencia a inicialização segura: valida modo sidecar → importa bridge → aplica shields → inicia app |
| `bridge.py` | 20+ funções `@eel.expose` (diálogos nativos, operações de arquivos, updates) + lógica sidecar de update |
| `folder_engine.py` | `FolderEngine`: scan recursivo, criação/atualização/espelhamento/cópia/deleção de estruturas, persistência em AppData |
| `version_control.py` | `VersionManager`: consulta GitHub API, download em stream com progress callback, verificação de hash |
| `shield.py` | 11 controles SEC: sanitiza XSS em nomes de pastas, valida URLs GitHub, valida `installer_path` em `%TEMP%` |
| `shield2.py` | CSP completa + 5 headers HTTP de segurança + injeção do `security.js` sem tocar o `index.html` |
| `window_manager.py` | Ciclo de reforço (60 tentativas) para fixar AppUserModelID e ícone via API COM do Windows |

---

### Fluxo de atualização (modo Sidecar)
1. Frontend solicita download → `bridge.executar_download_e_atualizar()` salva em `%TEMP%`
2. Frontend confirma → `bridge.finalizar_e_instalar()` copia o próprio `.exe` para `%TEMP%` e o relança com flag `--sidecar-mode`
3. A cópia neutra mata o processo principal e abre o instalador Inno Setup
4. Instalador substitui o binário original

---

### Build
- `build.ps1` → PyInstaller com `StructureBuilderPro.spec` → `dist/StructureBuilderPro.exe`
- Inno Setup com `installer_config.iss` → `output_installer/StructureBuilderPro_Setup_v5.6.2.exe`
- Persistência isolada: `%LOCALAPPDATA%\StructureBuilderPro` (prod) / `_DEV` (dev)

---

### Módulo: Renomeação em Massa

**Localização na sidebar:** abaixo de "Espelhamento de Pastas"

**Correção Técnica v1.1 (Independência de Layout):**
- **Exclusividade de Estados:** O menu foi atualizado para garantir independência total. Ao ser acionado, ele limpa explicitamente o estado `active` de botões vizinhos (como o de Espelhamento).
- **Auto-Ocultação (Vigilante de UI):** Implementado um mecanismo de escuta interna que oculta automaticamente a seção de Renomeação caso o usuário navegue para o Espelhamento ou utilize funções do menu principal (Carregar, Limpar).
- **Integridade de Módulos:** A solução foi aplicada estritamente no controlador da Renomeação, preservando o código homologado do Espelhamento sem qualquer modificação funcional.

**Fluxo do usuário:**
1. Seleciona uma **pasta modelo** → Structure Builder detecta o nome como padrão de busca
2. Preenche o **novo nome** que substituirá o padrão
3. Seleciona a **unidade/raiz de busca** (local ou servidor de rede)
4. Clica em **Buscar Pastas em Profundidade** → varredura recursiva completa via `os.walk`
5. Visualiza a lista de todas as pastas encontradas com o padrão
6. Confirma → **Aplicar Renomeação**

**O que acontece ao aplicar:**
- Para cada pasta encontrada:
  1. Cria nova pasta com o novo nome no **mesmo diretório pai**
  2. Copia todo o conteúdo da pasta original para a nova
  3. Move a pasta original para uma subpasta `Antigos` (criada automaticamente no mesmo pai)
- Relatório final exibe sucesso e erros individuais

**Arquivos alterados:**
| Arquivo | Alteração |
|---|---|
| `web/index.html` | Botão na sidebar + seção com 2 cards (Configuração 3 passos + Resultados) |
| `web/script.js` | Módulo `RENOMEAÇÃO EM MASSA` (navegação, validações, busca, confirmação, relatório) |
| `web/style.css` | Estilos dedicados: `.mr-container`, `.mr-step`, `.mr-badge`, `.mr-result-item`, etc. |
| `bridge.py` | 4 funções `@eel.expose`: `mr_selecionar_pasta_modelo`, `mr_selecionar_raiz_busca`, `mr_buscar_pastas`, `mr_aplicar_renomeacao` |

---

### Módulo: Manual In-App (Integrado)

**Localização na sidebar:** Botão "Manual" (abaixo de Verificar Atualização)

**Arquitetura de Visualização Nativa:**
- **Recurso Local:** O arquivo `manual.html` foi movido para `web/manual.html`, tornando-se um recurso servido internamente pelo motor do Eel.
- **Interface (Overlay):** Implementado um modal de tela cheia com *Glassmorphism* (`manual-modal`) contendo um `<iframe>` para renderização imediata.
- **Controle de Memória:** O `src` do iframe é definido como `manual.html` apenas ao abrir e limpo para `about:blank` ao fechar, otimizando o consumo de recursos.

**Segurança (Camada Shield):**
- **CSP (shield2.py):** Atualizada a diretiva `frame-src` de `'none'` para `'self'`. Isso permite que o software renderize seu próprio manual em um frame interno, mantendo o bloqueio rigoroso contra injeções de frames externos.

**Arquivos alterados:**
| Arquivo | Alteração |
|---|---|
| `shield2.py` | Autorização de frames locais via Content Security Policy (`frame-src 'self'`). |
| `web/index.html` | Adição da estrutura do `manual-modal` e do `manual-frame`. |
| `web/style.css` | Estilização premium do modal (blur, transparência, responsividade). |
| `web/script.js` | Lógica de controle: abertura do modal, carregamento do iframe e limpeza de estado. |
| `web/manual.html` | Movido da raiz para o diretório `/web` para integração com o servidor local. |
