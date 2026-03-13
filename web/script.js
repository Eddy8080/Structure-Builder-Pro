/**
 * Script Principal de Interface v5.3 - Registry-Based Workspace
 */

let state = {
    baseDir: "",
    mainFolder: "",
    tree: null, 
    selectedId: null,
    selectedTemplateIdx: null,
    originalState: null,
    isExistingStructure: false,
    isEditingTemplate: false
};

document.addEventListener('DOMContentLoaded', () => {
    carregarModelos();
    configurarEventos();
    configurarAtalhos();
    configurarMenuContexto();
    inicializarTema();
    restaurarMirroringState();
    configurarEventosMirror(); 
    verificarAtualizacaoSilenciosa(); // Engenharia Sênior: Verificação na inicialização
});

async function verificarAtualizacaoSilenciosa() {
    try {
        const res = await eel.verificar_atualizacao_disponivel()();
        if (res && res.has_update) {
            const btn = document.getElementById('btn-check-update');
            if (btn) btn.classList.add('update-available');
        }
    } catch (e) { console.error("Erro na verificação silenciosa:", e); }
}

async function executarVerificacaoManual() {
    mostrarLoader("Consultando servidor...");
    try {
        const res = await eel.verificar_atualizacao_disponivel()();
        esconderLoader();
        
        if (res.error) {
            alertar("Aviso", "Não foi possível conectar ao servidor de atualizações.", 'warning');
            return;
        }

        if (res.has_update) {
            const btn = document.getElementById('btn-check-update');
            if (btn) btn.classList.add('update-available');

            const confirm = await Swal.fire({
                title: 'Nova Atualização!',
                html: `
                    <div style="text-align: left; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; margin-top: 10px;">
                        <p><b>Versão disponível:</b> <span style="color: #fbbf24">${res.remote_version}</span></p>
                        <p><b>Sua versão:</b> ${res.local_version}</p>
                        <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 10px 0;">
                        <p style="font-size: 0.9rem; color: #94a3b8">${res.changelog}</p>
                    </div>
                    <p style="margin-top: 15px;">Deseja aplicar as melhorias agora?</p>
                `,
                icon: 'info',
                showCancelButton: true,
                confirmButtonText: 'Sim, Atualizar',
                cancelButtonText: 'Agora não',
                confirmButtonColor: '#10b981',
                cancelButtonColor: '#64748b',
                background: document.body.classList.contains('light-theme') ? '#ffffff' : '#1e293b',
                color: document.body.classList.contains('light-theme') ? '#1e293b' : '#f1f5f9'
            });

            if (confirm.isConfirmed) {
                mostrarLoader("Baixando atualização...");
                // Busca o executável nos assets da release do GitHub
                const assetExe = res.assets.find(a => a.name.endsWith('.exe'));
                if (assetExe) {
                    const downloadUrl = assetExe.browser_download_url;
                    const resUpdate = await eel.executar_download_e_atualizar(downloadUrl)();
                    if (resUpdate && resUpdate.error) {
                        esconderLoader();
                        alertar("Erro no Update", resUpdate.error, 'error');
                    }
                } else {
                    esconderLoader();
                    alertar("Erro", "Arquivo executável não encontrado no GitHub.", 'error');
                }
            }
        } else {
            const btn = document.getElementById('btn-check-update');
            if (btn) btn.classList.remove('update-available');
            
            const msg = res.info || 'Você já está na versão mais recente!';
            Toast.fire({ icon: 'success', title: msg });
        }
    } catch (e) {
        esconderLoader();
        alertar("Erro", "Falha na comunicação com o motor de atualização.", 'error');
    }
}

function sincronizarCamposDaTela() {
    state.mainFolder = document.getElementById('main-folder').value.trim();
    state.baseDir = document.getElementById('base-dir').value.trim();
    if (state.tree && state.mainFolder) {
        state.tree.name = state.mainFolder;
    }
}

function inicializarTema() {
    const theme = localStorage.getItem('app-theme') || 'dark';
    if (theme === 'light') { document.body.classList.add('light-theme'); atualizarIconeTema('sun'); }
    const btn = document.getElementById('btn-theme-toggle');
    if (btn) {
        btn.onclick = () => {
            const isLight = document.body.classList.toggle('light-theme');
            localStorage.setItem('app-theme', isLight ? 'light' : 'dark');
            atualizarIconeTema(isLight ? 'sun' : 'moon');
            Swal.update({ background: isLight ? '#ffffff' : '#1e293b', color: isLight ? '#1e293b' : '#f1f5f9' });
        };
    }
}

function atualizarIconeTema(iconName) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.setAttribute('data-lucide', iconName);
        lucide.createIcons();
    }
}

const Toast = Swal.mixin({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000 });

function alertar(titulo, texto, tipo = 'info') {
    const isLight = document.body.classList.contains('light-theme');
    return Swal.fire({ title: titulo, text: texto, icon: tipo, confirmButtonColor: '#3b82f6', background: isLight ? '#ffffff' : '#1e293b', color: isLight ? '#1e293b' : '#f1f5f9' });
}

async function confirmar(titulo, texto, tipo = 'warning') {
    const isLight = document.body.classList.contains('light-theme');
    const result = await Swal.fire({ title: titulo, text: texto, icon: tipo, showCancelButton: true, confirmButtonColor: '#10b981', cancelButtonColor: '#ef4444', confirmButtonText: 'Sim', cancelButtonText: 'Não', background: isLight ? '#ffffff' : '#1e293b', color: isLight ? '#1e293b' : '#f1f5f9' });
    return result.isConfirmed;
}

function configurarEventos() {
    document.getElementById('btn-select-base').onclick = async () => {
        const path = await eel.selecionar_pasta("Diretório Base")();
        if (path) { state.baseDir = path; document.getElementById('base-dir').value = path; }
    };

    document.getElementById('btn-load').onclick = async () => {
        const path = await eel.selecionar_pasta("Abrir Pasta")();
        if (path) {
            mostrarLoader("Lendo estrutura...");
            const dados = await eel.carregar_estrutura_existente(path)();
            esconderLoader();
            if (dados.error) alertar("Erro", dados.error, 'error');
            else { aplicarDadosAoEstado(dados); state.isExistingStructure = true; state.isEditingTemplate = false; atualizarUIModo(true); }
        }
    };

    document.getElementById('btn-apply').onclick = async () => {
        sincronizarCamposDaTela();
        mostrarLoader("Sincronizando com Windows...");
        const res = await eel.sincronizar_no_windows(state.baseDir, state.mainFolder, state.tree, state.originalState, state.isExistingStructure)();
        if (res.error) { esconderLoader(); alertar("Aviso", res.error, 'warning'); return; }
        aplicarDadosAoEstado(res.fresh_data);
        state.isExistingStructure = true; 
        atualizarUIModo(true);
        esconderLoader();
        Toast.fire({ icon: 'success', title: 'Sincronizado!' });
    };

    document.getElementById('btn-apply-template').onclick = async () => {
        sincronizarCamposDaTela();
        mostrarLoader("Salvando modelo...");
        const res = await eel.atualizar_dados_modelo(state.selectedTemplateIdx, state.mainFolder, state.tree)();
        esconderLoader();
        if (res === true) { Toast.fire({ icon: 'success', title: 'Modelo atualizado!' }); carregarModelos(); }
        else alertar("Erro", res, 'error');
    };

    document.getElementById('btn-quick-save').onclick = async () => {
        sincronizarCamposDaTela();
        const isLight = document.body.classList.contains('light-theme');
        const { value: customName } = await Swal.fire({
            title: 'Nome da Pasta Raiz',
            text: 'Como a pasta raiz deve ser chamada no Windows Explorer?',
            input: 'text',
            inputValue: state.mainFolder, 
            showCancelButton: true,
            confirmButtonColor: '#3b82f6',
            confirmButtonText: 'Continuar',
            cancelButtonText: 'Cancelar',
            background: isLight ? '#ffffff' : '#1e293b',
            color: isLight ? '#1e293b' : '#f1f5f9',
            inputValidator: (value) => {
                if (!value) return 'Você precisa definir um nome para a pasta!';
            }
        });
        if (!customName) return;
        const target = await eel.selecionar_pasta("Onde criar?")();
        if (target) {
            mostrarLoader("Criando...");
            const res = await eel.sincronizar_no_windows(target, customName.trim(), state.tree, null, false)();
            esconderLoader();
            if (res.error) alertar("Erro", res.error, 'error');
            else alertar("Sucesso", `Estrutura criada com sucesso em: ${res.path}`, 'success');
        }
    };

    document.getElementById('btn-save-template').onclick = async () => {
        sincronizarCamposDaTela();
        const path = await eel.selecionar_arquivo_salvar("Exportar Estrutura Atual")();
        if (path) {
            const dados = { main_folder: state.mainFolder, tree_structure: state.tree };
            const ok = await eel.salvar_modelo_arquivo(path, [dados])();
            if (ok === true) alertar("Sucesso", "Estrutura exportada!", 'success');
            else alertar("Erro", ok, 'error');
        }
    };

    document.getElementById('btn-backup-library').onclick = async () => {
        const path = await eel.selecionar_arquivo_salvar("Salvar Backup da Biblioteca", ".json")();
        if (path) {
            const modelos = await eel.obter_modelos_rapidos()();
            const ok = await eel.salvar_modelo_arquivo(path, modelos)();
            if (ok === true) alertar("Sucesso", "Backup concluído!", 'success');
            else alertar("Erro", ok, 'error');
        }
    };

    document.getElementById('btn-restore-library').onclick = async () => {
        const ok = await eel.restaurar_modelos_arquivo()();
        if (ok === true) {
            Toast.fire({ icon: 'success', title: 'Biblioteca Restaurada!' });
            carregarModelos();
        } else if (ok) alertar("Erro", ok, 'error');
    };

    document.getElementById('btn-create').onclick = () => executarAcaoFinal();
    document.getElementById('btn-update').onclick = () => executarAcaoFinal();
    document.getElementById('btn-check-update').onclick = executarVerificacaoManual;
    document.getElementById('btn-manual').onclick = async () => eel.abrir_manual()();
    document.getElementById('btn-clear').onclick = async () => { if (await confirmar("Limpar", "Reiniciar?")) resetarUI(); };

    const confirmarMainFolder = () => {
        const nome = document.getElementById('main-folder').value.trim();
        if (!nome) return;
        state.mainFolder = nome;
        if (!state.tree) { 
            state.tree = { name: nome, id: "root", isExpanded: true, children: [] };
            renderizarArvore(); 
        } else { 
            state.tree.name = nome;
            renderizarArvore(); 
        }
    };
    document.getElementById('btn-confirm-main').onclick = confirmarMainFolder;
    document.getElementById('main-folder').oninput = (e) => {
        const nome = e.target.value.trim();
        if (state.tree && nome) {
            state.tree.name = nome;
            state.mainFolder = nome;
            renderizarArvore();
        }
    };
    document.getElementById('main-folder').onkeydown = (e) => { if (e.key === 'Enter') confirmarMainFolder(); };
    document.getElementById('btn-new-folder').onclick = () => criarNovaPasta();
    document.getElementById('btn-diagram').onclick = gerarDiagrama;
    document.getElementById('btn-close-diagram').onclick = () => document.getElementById('diagram-modal').classList.add('hidden');
    document.getElementById('btn-download-diagram').onclick = baixarDiagramaSvg;
    document.getElementById('btn-add-template').onclick = async () => {
        const res = await eel.adicionar_modelo_rapido()();
        if (res && res.status === "success") carregarModelos();
    };
    document.addEventListener('click', (e) => {
        document.getElementById('context-menu').classList.add('hidden');
        document.getElementById('template-context-menu').classList.add('hidden');
        if (!e.target.closest('.template-item')) document.querySelectorAll('.template-item').forEach(el => el.classList.remove('selected'));
    });
}

function configurarAtalhos() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') document.querySelectorAll('.context-menu, .overlay, .rename-bar, .context-menu').forEach(el => el.classList.add('hidden'));
        
        if (mirroringState.isMirrorMode && mirroringState.selectedIds.length > 0) {
            if (e.key === 'F2') { e.preventDefault(); iniciarRenomeacaoMirror(); }
            if (e.key === 'Delete') { e.preventDefault(); removerPastaMirror(); }
        }

        if (state.selectedId) {
            if (e.key === 'F2') { e.preventDefault(); iniciarRenomeacao(); }
            if (e.key === 'Delete') { e.preventDefault(); removerPasta(state.selectedId); }
        }
        if (state.selectedTemplateIdx !== null && !state.selectedId) {
            if (e.key === 'Delete') { e.preventDefault(); removerModeloInterface(state.selectedTemplateIdx); }
            if (e.key === 'F2') { e.preventDefault(); renomearModeloInterface(state.selectedTemplateIdx); }
        }
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') { e.preventDefault(); criarNovaPasta(); }
        if (e.key === 'Enter' && !document.getElementById('rename-floating-bar').classList.contains('hidden')) confirmarRenomeacao();
    });
}

function buscarNode(node, id) {
    if (node.id === id) return node;
    for (let child of (node.children || [])) { const found = buscarNode(child, id); if (found) return found; }
    return null;
}

function compararPastas(a, b) { return a.name.localeCompare(b.name, 'pt-BR', { numeric: true, sensitivity: 'base' }); }

function criarNovaPasta() {
    if (!state.tree) return alertar("Aviso", "Defina a Pasta Principal.", 'warning');
    let targetParent = state.tree;
    if (state.selectedId) targetParent = buscarNode(state.tree, state.selectedId);
    const newId = "id_" + Date.now();
    targetParent.isExpanded = true;
    targetParent.children.push({ id: newId, name: "Nova Pasta", isExpanded: true, children: [] });
    targetParent.children.sort(compararPastas);
    renderizarArvore(); selecionarItem(newId); iniciarRenomeacao();
}

function removerPasta(id) {
    if (id === "root") return;
    const deletarRecursivo = (node) => {
        const idx = node.children.findIndex(c => c.id === id);
        if (idx !== -1) { node.children.splice(idx, 1); return true; }
        for (let child of node.children) { if (deletarRecursivo(child)) return true; }
        return false;
    };
    confirmar("Remover", "Deletar esta pasta?").then(ok => { if (ok) { deletarRecursivo(state.tree); state.selectedId = null; renderizarArvore(); } });
}

function renderizarArvore() {
    const container = document.getElementById('tree-container');
    if (!container) return;
    container.innerHTML = '';
    if (!state.tree) { container.innerHTML = '<div class="empty-tree-state"><p>Estrutura vazia.</p></div>'; return; }
    const montarHTML = (node, isRoot = false) => {
        const divNode = document.createElement('div'); divNode.className = "tree-node";
        const content = document.createElement('div');
        content.className = `tree-item-content ${state.selectedId === node.id ? 'selected' : ''}`;
        content.dataset.id = node.id;
        const hasChildren = node.children && node.children.length > 0;
        const toggleIcon = hasChildren ? `<i data-lucide="chevron-right" class="toggle-icon ${node.isExpanded ? 'expanded' : ''}" onclick="event.stopPropagation(); togglePasta('${node.id}')"></i>` : `<span class="toggle-placeholder"></span>`;
        content.innerHTML = `${toggleIcon}<i data-lucide="${isRoot ? 'folder-tree' : 'folder'}" class="folder-icon"></i><span>${node.name}</span>`;
        content.onclick = (e) => { e.stopPropagation(); selecionarItem(node.id); };
        content.ondblclick = (e) => { e.stopPropagation(); togglePasta(node.id); };
        divNode.appendChild(content);
        if (hasChildren) {
            const divChildren = document.createElement('div'); divChildren.className = "tree-children";
            if (!node.isExpanded) divChildren.classList.add('collapsed');
            node.children.sort(compararPastas);
            node.children.forEach(child => divChildren.appendChild(montarHTML(child)));
            divNode.appendChild(divChildren);
        }
        return divNode;
    };
    container.appendChild(montarHTML(state.tree, true));
    lucide.createIcons();
}

function togglePasta(id) { const node = buscarNode(state.tree, id); if (node) { node.isExpanded = !node.isExpanded; renderizarArvore(); } }
async function executarAcaoFinal() { sincronizarCamposDaTela(); document.getElementById('btn-apply').click(); setTimeout(() => { if (!document.querySelector('.swal2-shown')) resetarUI(); }, 1500); }
let renamingTargetId = null;
function aplicarDadosAoEstado(dados) {
    state.mainFolder = dados.main_folder || ""; state.originalState = dados;
    document.getElementById('base-dir').value = dados.base_dir || "";
    document.getElementById('main-folder').value = state.mainFolder;
    if (dados.tree_structure) { state.tree = prepararArvoreRecursiva(dados.tree_structure); state.tree.id = "root"; state.tree.isExpanded = true; }
    renderizarArvore();
}
function prepararArvoreRecursiva(node) {
    const newNode = { id: node.id || "id_" + Math.random().toString(36).substr(2, 9), name: node.name, isExpanded: node.isExpanded !== undefined ? node.isExpanded : false, children: (node.children || []).map(c => prepararArvoreRecursiva(c)) };
    newNode.children.sort(compararPastas);
    return newNode;
}
function atualizarUIModo(isUpdate) {
    const editMode = isUpdate || state.isEditingTemplate;
    const btnCreate = document.getElementById('btn-create');
    const btnUpdate = document.getElementById('btn-update');
    const btnTemplate = document.getElementById('btn-apply-template');
    if (btnCreate) btnCreate.classList.toggle('hidden', editMode);
    if (btnUpdate) btnUpdate.classList.toggle('hidden', !editMode);
    if (btnTemplate) btnTemplate.classList.toggle('hidden', !state.isEditingTemplate);
}
function resetarUI() {
    state = { baseDir: "", mainFolder: "", tree: null, selectedId: null, selectedTemplateIdx: null, originalState: null, isExistingStructure: false, isEditingTemplate: false };
    document.getElementById('base-dir').value = ""; document.getElementById('main-folder').value = "";
    atualizarUIModo(false); renderizarArvore();
}
function iniciarRenomeacao() {
    const bar = document.getElementById('rename-floating-bar'); const input = document.getElementById('rename-input'); const node = buscarNode(state.tree, state.selectedId);
    if (node && bar && input) { renamingTargetId = node.id; bar.classList.remove('hidden'); input.value = node.name; setTimeout(() => { input.focus(); input.select(); }, 10); }
    const btnConfirm = document.getElementById('btn-confirm-rename');
    if (btnConfirm) btnConfirm.onclick = confirmarRenomeacao;
}
function confirmarRenomeacao() {
    const input = document.getElementById('rename-input'); const novoNome = input ? input.value.trim() : "";
    if (renamingTargetId && novoNome !== "") {
        const node = buscarNode(state.tree, renamingTargetId);
        if (node) { node.name = novoNome; if (node.id === "root") { state.mainFolder = node.name; document.getElementById('main-folder').value = node.name; } }
    }
    renamingTargetId = null; 
    const bar = document.getElementById('rename-floating-bar');
    if (bar) bar.classList.add('hidden'); 
    renderizarArvore();
}
function selecionarItem(id) { state.selectedId = id; renderizarArvore(); }
async function carregarModelos() {
    const modelos = await eel.obter_modelos_rapidos()(); const list = document.getElementById('templates-list'); if (!list) return; list.innerHTML = '';
    modelos.forEach((m, idx) => {
        const item = document.createElement('div'); item.className = 'template-item'; if (state.selectedTemplateIdx === idx) item.classList.add('selected');
        item.innerHTML = `<i data-lucide="folder"></i> <span>${m.main_folder}</span>`;
        item.onclick = (e) => { e.stopPropagation(); state.selectedTemplateIdx = idx; state.selectedId = null; state.isExistingStructure = false; state.isEditingTemplate = true; document.querySelectorAll('.template-item').forEach(el => el.classList.remove('selected')); item.classList.add('selected'); aplicarModelo(m); atualizarUIModo(true); };
        item.oncontextmenu = (e) => { e.preventDefault(); e.stopPropagation(); state.selectedTemplateIdx = idx; document.querySelectorAll('.template-item').forEach(el => el.classList.remove('selected')); item.classList.add('selected'); mostrarMenuModelo(e, idx); };
        list.appendChild(item);
    });
    lucide.createIcons();
}
function mostrarMenuModelo(e, index) {
    const menu = document.getElementById('template-context-menu'); if (!menu) return;
    menu.style.top = `${e.clientY}px`; menu.style.left = `${e.clientX}px`; menu.classList.remove('hidden');
    document.getElementById('tm-rename').onclick = () => renomearModeloInterface(index); document.getElementById('tm-delete').onclick = () => removerModeloInterface(index);
}
async function renomearModeloInterface(index) {
    const modelos = await eel.obter_modelos_rapidos()();
    const { value: novoNome } = await Swal.fire({ title: 'Renomear', input: 'text', inputValue: modelos[index].main_folder, showCancelButton: true, confirmButtonColor: '#3b82f6', background: document.body.classList.contains('light-theme') ? '#ffffff' : '#1e293b', color: document.body.classList.contains('light-theme') ? '#1e293b' : '#f1f5f9' });
    if (novoNome && novoNome.trim() !== "") { 
        const nomeFinal = novoNome.trim(); await eel.renomear_modelo_rapido(index, nomeFinal)(); 
        if (state.selectedTemplateIdx === index) { state.mainFolder = nomeFinal; document.getElementById('main-folder').value = nomeFinal; if (state.tree) { state.tree.name = nomeFinal; renderizarArvore(); } }
        carregarModelos(); 
    }
}
async function removerModeloInterface(index) { if (await confirmar("Remover", "Remover este modelo?")) { await eel.remover_modelo_rapido(index)(); state.selectedTemplateIdx = null; carregarModelos(); } }
function aplicarModelo(modelo) { aplicarDadosAoEstado(modelo); }
function configurarMenuContexto() {
    const menu = document.getElementById('context-menu');
    const treeContainer = document.getElementById('tree-container');
    if (treeContainer && menu) {
        treeContainer.oncontextmenu = (e) => {
            e.preventDefault(); const itemElement = e.target.closest('.tree-item-content');
            if (itemElement) selecionarItem(itemElement.dataset.id); else { state.selectedId = null; renderizarArvore(); }
            menu.style.top = `${e.clientY}px`; menu.style.left = `${e.clientX}px`; menu.classList.remove('hidden');
        };
    }
    const btnNew = document.getElementById('cm-new');
    const btnRen = document.getElementById('cm-rename');
    const btnDel = document.getElementById('cm-delete');
    if (btnNew) btnNew.onclick = () => criarNovaPasta(); 
    if (btnRen) btnRen.onclick = () => iniciarRenomeacao(); 
    if (btnDel) btnDel.onclick = () => removerPasta(state.selectedId);
}
function mostrarLoader(msg) { const ov = document.getElementById('loader-overlay'); const m = document.getElementById('loader-message'); if (ov && m) { m.innerText = msg; ov.classList.remove('hidden'); } }
function esconderLoader() { const ov = document.getElementById('loader-overlay'); if (ov) ov.classList.add('hidden'); }
async function gerarDiagrama() {
    if (!state.tree) return;
    const modal = document.getElementById('diagram-modal'); const container = document.getElementById('mermaid-container');
    if (!modal || !container) return;
    modal.classList.remove('hidden'); container.innerHTML = '<div class="spinner"></div>';
    mermaid.initialize({ startOnLoad: false, theme: document.body.classList.contains('light-theme') ? 'default' : 'dark', securityLevel: 'loose' });
    let mermaidText = "graph LR\n"; mermaidText += "classDef root fill:#3b82f6,stroke:#2563eb,color:#fff,stroke-width:2px;\n"; mermaidText += "classDef folder fill:#1e293b,stroke:#3b82f6,color:#f1f5f9;\n";
    const processNode = (node, isRoot = false) => {
        const id = node.id.replace(/-/g, "_"); const name = `"${node.name.replace(/"/g, "'")}"`;
        mermaidText += `  ${id}[${name}]\n`; mermaidText += `  class ${id} ${isRoot ? 'root' : 'folder'}\n`;
        node.children.forEach(child => { const childId = child.id.replace(/-/g, "_"); mermaidText += `  ${id} --> ${childId}\n`; processNode(child); });
    };
    processNode(state.tree, true);
    try { const { svg } = await mermaid.render('mermaid-svg', mermaidText); container.innerHTML = svg; } catch (error) { console.error("Erro Mermaid:", error); container.innerHTML = `<p style="color:red">Erro visual.</p>`; }
}
function baixarDiagramaSvg() {
    const svgElement = document.querySelector('#mermaid-container svg'); if (!svgElement) return;
    const downloadLink = document.createElement("a"); downloadLink.href = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svgElement)], { type: "image/svg+xml;charset=utf-8" }));
    downloadLink.download = `${state.mainFolder || 'estrutura'}_diagrama.svg`; document.body.appendChild(downloadLink); downloadLink.click(); document.body.removeChild(downloadLink);
}

// --- MÓDULO DE ESPELHAMENTO (MULTIPLE SNAPSHOT REGISTRY) ---

const mirroringState = { 
    basePath: "", editableTree: null, syncedTree: null, 
    selectedIds: [], draggedIds: [], isMirrorMode: false,
    lastUpdate: null, history: {},
    pinnedSnapshots: {} 
};

function configurarEventosMirror() {
    const btnMenu = document.getElementById('btn-mirroring-menu');
    if (btnMenu) btnMenu.onclick = () => {
        mirroringState.isMirrorMode = true;
        document.getElementById('mirroring-section').classList.remove('hidden');
        document.getElementById('main-menu-section').classList.add('hidden');
        btnMenu.classList.add('active');
        if (mirroringState.editableTree) renderizarArvoresEspelhamento();
        atualizarVisibilidadeBotaoRecall();
        setTimeout(inicializarResizerUnificado, 100);
    };
    const btnBack = document.getElementById('btn-back-to-main');
    if (btnBack) btnBack.onclick = () => {
        mirroringState.isMirrorMode = false;
        document.getElementById('mirroring-section').classList.add('hidden');
        document.getElementById('main-menu-section').classList.remove('hidden');
        document.getElementById('btn-mirroring-menu').classList.remove('active');
    };
    document.getElementById('btn-mirror-load').onclick = async () => {
        const path = await eel.selecionar_pasta("Selecionar Pasta")();
        if (path) {
            mostrarLoader("Mapeando...");
            try {
                const dados = await eel.carregar_estrutura_existente(path, true)();
                if (dados.error) { alertar("Erro", dados.error, 'error'); return; }
                mirroringState.basePath = path;
                if (mirroringState.history[path]) { mirroringState.editableTree = mirroringState.history[path].tree; mirroringState.lastUpdate = mirroringState.history[path].lastUpdate; }
                else { mirroringState.editableTree = prepararArvoreEspelhamento(dados.tree_structure, true); mirroringState.lastUpdate = null; }
                atualizarLabelData(mirroringState.lastUpdate); mirroringState.syncedTree = JSON.parse(JSON.stringify(mirroringState.editableTree));
                atualizarVisibilidadeBotaoRecall();
                renderizarArvoresEspelhamento(); persistirMirroringState();
            } catch (err) { alertar("Erro", "Falha ao carregar."); } finally { esconderLoader(); }
        }
    };
    document.getElementById('btn-mirror-remember').onclick = salvarLembrancaMirror;
    document.getElementById('btn-mirror-recall').onclick = restaurarLembrancaMirror;
    document.getElementById('btn-mirror-apply').onclick = async () => {
        if (!mirroringState.editableTree) return;
        mostrarLoader("Sincronizando...");
        try {
            const res = await eel.aplicar_espelhamento(mirroringState.basePath, mirroringState.editableTree)();
            if (res.error) alertar("Erro", res.error, 'error');
            else {
                mirroringState.basePath = res.new_structure.full_path;
                const mark = (n, isRoot) => { 
                    if (isRoot || n.status === "pending") n.status = "applied"; 
                    else if (!n.status) n.status = "idle";
                    if (n.children) n.children.forEach(c => mark(c, false)); 
                };
                mark(mirroringState.editableTree, true); 
                const dataFormatada = new Date().toLocaleString('pt-BR');
                mirroringState.lastUpdate = dataFormatada; atualizarLabelData(dataFormatada);
                mirroringState.syncedTree = JSON.parse(JSON.stringify(mirroringState.editableTree));
                renderizarArvoresEspelhamento(); persistirMirroringState(); 
                Toast.fire({ icon: 'success', title: 'Sincronizado!' });
            }
        } catch (err) { alertar("Erro", "Falha na comunicação."); }
        finally { esconderLoader(); }
    };
    document.getElementById('btn-mirror-clear').onclick = () => {
        mirroringState.basePath = ""; mirroringState.editableTree = null; mirroringState.syncedTree = null; mirroringState.lastUpdate = null;
        atualizarLabelData(null);
        const t1 = document.getElementById('mirror-tree-editable');
        const t2 = document.getElementById('mirror-tree-synced');
        if (t1) t1.innerHTML = ''; 
        if (t2) t2.innerHTML = ''; 
        persistirMirroringState();
    };
    const menu = document.getElementById('mirror-context-menu');
    const mirrorContainer = document.getElementById('mirror-tree-editable');
    if (mirrorContainer && menu) {
        mirrorContainer.oncontextmenu = (e) => {
            e.preventDefault(); const item = e.target.closest('.tree-item-content') || e.target.closest('.file-item-mirror');
            if (item) { selecionarItemMirror(item.dataset.id); menu.style.top = `${e.clientY}px`; menu.style.left = `${e.clientX}px`; menu.classList.remove('hidden'); }
        };
    }
    document.getElementById('mcm-new').onclick = criarNovaPastaMirror; 
    document.getElementById('mcm-rename').onclick = iniciarRenomeacaoMirror; 
    document.getElementById('mcm-delete').onclick = removerPastaMirror;
}

function salvarLembrancaMirror() {
    if (!mirroringState.editableTree || !mirroringState.basePath) {
        Toast.fire({ icon: 'warning', title: 'Nada para lembrar!' });
        return;
    }
    mirroringState.pinnedSnapshots[mirroringState.basePath] = {
        tree: JSON.parse(JSON.stringify(mirroringState.editableTree)),
        lastUpdate: mirroringState.lastUpdate,
        folderName: mirroringState.editableTree.name,
        timestamp: new Date().getTime()
    };
    persistirMirroringState();
    atualizarVisibilidadeBotaoRecall();
    Toast.fire({ icon: 'success', title: 'Lembrança salva!' });
}

async function restaurarLembrancaMirror() {
    const chaves = Object.keys(mirroringState.pinnedSnapshots);
    if (chaves.length === 0) { Toast.fire({ icon: 'info', title: 'Nenhuma lembrança.' }); return; }

    // Engenharia Sênior: Central de Gestão de Memórias (Contraste e Gestão)
    let listHtml = `<div class="memory-management-list">`;
    chaves.sort((a,b) => mirroringState.pinnedSnapshots[b].timestamp - mirroringState.pinnedSnapshots[a].timestamp).forEach(path => {
        const snap = mirroringState.pinnedSnapshots[path];
        const data = new Date(snap.timestamp).toLocaleString('pt-BR');
        listHtml += `
            <div class="memory-item" onclick="window.confirmarRestauracaoMemory('${path.replace(/\\/g, '/')}')">
                <button class="delete-memory-btn" onclick="event.stopPropagation(); window.deletarMemory('${path.replace(/\\/g, '/')}')" title="Excluir Lembrança">×</button>
                <div class="memory-info">
                    <span class="memory-name">${snap.folderName}</span>
                    <span class="memory-date">${data}</span>
                </div>
            </div>
        `;
    });
    listHtml += `</div>`;

    window.confirmarRestauracaoMemory = (p) => { 
        const path = p;
        Swal.close(); 
        if (mirroringState.pinnedSnapshots[path]) {
            aplicarSnapshotMirror(path, mirroringState.pinnedSnapshots[path]); 
            Toast.fire({ icon: 'success', title: 'Projeto recuperado!' }); 
        }
    };

    window.deletarMemory = async (p) => { 
        const path = p;
        if (await confirmar("Excluir", `Remover lembrança de "${mirroringState.pinnedSnapshots[path].folderName}"?`)) {
            delete mirroringState.pinnedSnapshots[path];
            persistirMirroringState();
            atualizarVisibilidadeBotaoRecall();
            Swal.close();
            setTimeout(restaurarLembrancaMirror, 100);
        }
    };

    await Swal.fire({
        title: 'Recarregar Lembrança',
        html: listHtml,
        showConfirmButton: false,
        showCancelButton: true,
        cancelButtonText: 'Fechar',
        background: document.body.classList.contains('light-theme') ? '#ffffff' : '#1e293b',
        color: document.body.classList.contains('light-theme') ? '#1e293b' : '#f1f5f9'
    });
}

function aplicarSnapshotMirror(path, snapshot) {
    mirroringState.basePath = path;
    mirroringState.editableTree = JSON.parse(JSON.stringify(snapshot.tree));
    mirroringState.lastUpdate = snapshot.lastUpdate;
    mirroringState.syncedTree = JSON.parse(JSON.stringify(mirroringState.editableTree));
    atualizarLabelData(mirroringState.lastUpdate);
    recalcularContagensVirtuais(mirroringState.editableTree);
    renderizarArvoresEspelhamento();
    persistirMirroringState();
}

function atualizarVisibilidadeBotaoRecall() {
    const btn = document.getElementById('btn-mirror-recall');
    if (btn) {
        const has = Object.keys(mirroringState.pinnedSnapshots).length > 0;
        btn.classList.toggle('hidden', !has);
    }
}

function renderizarArvoreMirror(tree, containerId, isEditable) {
    const container = document.getElementById(containerId); if (!container || !tree) return; container.innerHTML = '';
    const montarHTML = (node, isRoot = false) => {
        const divNode = document.createElement('div'); divNode.className = "tree-node"; const content = document.createElement('div');
        const isSelected = mirroringState.selectedIds.includes(node.id);
        let sClass = node.status === "applied" ? "status-applied" : (node.status === "pending" ? "status-pending" : "");
        if (node.type === "file") {
            content.className = `file-item-mirror ${isSelected ? 'selected-multiple' : ''} ${sClass}`;
            content.innerHTML = `<i data-lucide="file-text"></i><span class="file-name-text">${node.name}</span>`;
        } else {
            content.className = `tree-item-content ${isSelected ? 'selected-multiple' : ''} ${isRoot ? 'mirror-root-item' : ''} ${sClass}`;
            const hasChildren = node.children && node.children.length > 0;
            const toggleIcon = hasChildren ? `<i data-lucide="chevron-right" class="toggle-icon ${node.isExpanded ? 'expanded' : ''}" onclick="event.stopPropagation(); toggleMirrorNode('${node.id}')"></i>` : `<span class="toggle-placeholder"></span>`;
            
            // Engenharia Sênior: Unificação de Indicadores
            // O contador central passa a exibir o Total Recursivo, eliminando a poluição visual da badge externa.
            const localCount = `<span class="local-count">${node.total_file_count || 0}</span>`;
            
            content.innerHTML = `${toggleIcon}<div class="${isRoot ? 'mirror-root-container' : 'subfolder-stack'}"><i data-lucide="${isRoot ? 'folder-tree' : 'folder'}" class="folder-icon"></i>${localCount}</div><span class="folder-name-text">${node.name}</span>`;
        }
        content.dataset.id = node.id; content.draggable = isEditable;
        content.onclick = (e) => { e.stopPropagation(); selecionarItemMirror(node.id); };
        if (node.type !== "file") content.ondblclick = () => toggleMirrorNode(node.id);
        if (isEditable) {
            content.ondragstart = (e) => { mirroringState.draggedIds = [node.id]; e.dataTransfer.setData('text/plain', node.id); };
            content.ondragover = (e) => { 
                e.preventDefault(); 
                if (node.type !== "file") content.classList.add('drop-target'); 
                
                // Engenharia Sênior: Auto-Scroll Dinâmico
                const scrollContainer = document.getElementById('mirror-tree-editable');
                if (scrollContainer) {
                    const rect = scrollContainer.getBoundingClientRect();
                    const threshold = 50; // pixels da borda
                    if (e.clientY < rect.top + threshold) scrollContainer.scrollTop -= 8;
                    else if (e.clientY > rect.bottom - threshold) scrollContainer.scrollTop += 8;
                }
            };
            content.ondragleave = () => content.classList.remove('drop-target');
            content.ondrop = (e) => {
                e.preventDefault(); content.classList.remove('drop-target'); if (node.type === "file") return;
                let moved = false;
                mirroringState.draggedIds.forEach(id => {
                    if (id === node.id) return;
                    const source = findMirrorNode(mirroringState.editableTree, id);
                    if (!source || !findMirrorParent(mirroringState.editableTree, id)) return;
                    
                    if (source.type === "directory") {
                        // Engenharia Sênior: A pasta de origem age como container e NÃO é deletada.
                        // Extraímos e removemos apenas os arquivos (recursivamente).
                        const extrairERemover = (n) => {
                            let fs = [];
                            if (n.children) {
                                for (let i = n.children.length - 1; i >= 0; i--) {
                                    const c = n.children[i];
                                    if (c.type === "file") {
                                        fs.push(n.children.splice(i, 1)[0]);
                                    } else {
                                        fs = fs.concat(extrairERemover(c));
                                    }
                                }
                            }
                            return fs;
                        };
                        const files = extrairERemover(source);
                        files.forEach(f => { f.status = "pending"; node.children.push(f); moved = true; });
                    } else { 
                        // Se for um arquivo isolado, remove do pai e transfere
                        const parent = findMirrorParent(mirroringState.editableTree, id);
                        const idx = parent.children.findIndex(c => c.id === id);
                        const sourceItem = parent.children.splice(idx, 1)[0];
                        sourceItem.status = "pending"; 
                        node.children.push(sourceItem); 
                        moved = true; 
                    }
                });
                if (moved) { recalcularContagensVirtuais(mirroringState.editableTree); mirroringState.syncedTree = JSON.parse(JSON.stringify(mirroringState.editableTree)); renderizarArvoresEspelhamento(); persistirMirroringState(); }
            };
        }
        divNode.appendChild(content);
        if (node.type !== "file" && node.isExpanded && node.children) {
            const divChildren = document.createElement('div'); divChildren.className = "tree-children";
            node.children.sort((a,b) => (a.type !== b.type ? (a.type === "directory" ? -1 : 1) : a.name.localeCompare(b.name, 'pt-BR', { numeric: true }))).forEach(child => divChildren.appendChild(montarHTML(child)));
            divNode.appendChild(divChildren);
        }
        return divNode;
    };
    container.appendChild(montarHTML(tree, true)); lucide.createIcons();
}

function findMirrorNode(node, id) { if (!node) return null; if (node.id === id) return node; for (let c of (node.children || [])) { const f = findMirrorNode(c, id); if (f) return f; } return null; }
function findMirrorParent(node, id) { if (!node || !node.children) return null; for (let c of node.children) { if (c.id === id) return node; const f = findMirrorParent(c, id); if (f) return f; } return null; }
function toggleMirrorNode(id) { const n = findMirrorNode(mirroringState.editableTree, id); if (n) { n.isExpanded = !n.isExpanded; mirroringState.syncedTree = JSON.parse(JSON.stringify(mirroringState.editableTree)); renderizarArvoresEspelhamento(); } }
function selecionarItemMirror(id) {
    mirroringState.selectedIds = [id];
    const expandir = (node, tid) => { if (node.id === tid) return true; if (node.children) { for (let c of node.children) { if (expandir(c, tid)) { node.isExpanded = true; return true; } } } return false; };
    if (mirroringState.editableTree) expandir(mirroringState.editableTree, id);
    mirroringState.syncedTree = JSON.parse(JSON.stringify(mirroringState.editableTree));
    renderizarArvoresEspelhamento();
    setTimeout(() => { const els = document.querySelectorAll(`[data-id="${id}"]`); els.forEach(el => el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })); }, 50);
}
function prepararArvoreEspelhamento(n, isRoot = false) { return { id: n.id || "m_"+Math.random().toString(36).substr(2,9), name: n.name, type: n.type||"directory", full_path: n.full_path, isExpanded: isRoot, file_count: n.file_count||0, total_file_count: n.total_file_count||0, status: null, children: (n.children||[]).map(c => prepararArvoreEspelhamento(c, false)) }; }
function recalcularContagensVirtuais(n) { let l=0, t=0; if (n.children) n.children.forEach(c => { if (c.type === "file") { l++; t++; } else t += recalcularContagensVirtuais(c); }); n.file_count=l; n.total_file_count=t; return t; }
function atualizarLabelData(d) { const c = document.getElementById('mirror-last-update-container'), l = document.getElementById('mirror-last-update-date'); if (d && c && l) { l.innerText = d; c.classList.remove('hidden'); } else if (c) c.classList.add('hidden'); }

async function persistirMirroringState() { 
    if (mirroringState.editableTree && mirroringState.basePath) { mirroringState.history[mirroringState.basePath] = { lastUpdate: mirroringState.lastUpdate, tree: mirroringState.editableTree }; }
    await eel.salvar_estado_espelhamento({ history: mirroringState.history, activePath: mirroringState.basePath, isMirrorMode: mirroringState.isMirrorMode, pinnedSnapshots: mirroringState.pinnedSnapshots })(); 
}
async function restaurarMirroringState() { 
    try { 
        const d = await eel.carregar_estado_espelhamento()(); 
        if (d) {
            mirroringState.history = d.history || {}; 
            mirroringState.pinnedSnapshots = d.pinnedSnapshots || {};
            atualizarVisibilidadeBotaoRecall();
            if (d.activePath && mirroringState.history[d.activePath]) {
                mirroringState.basePath = d.activePath;
                mirroringState.editableTree = mirroringState.history[d.activePath].tree;
                mirroringState.lastUpdate = mirroringState.history[d.activePath].lastUpdate;
                mirroringState.syncedTree = JSON.parse(JSON.stringify(mirroringState.editableTree));
                atualizarLabelData(mirroringState.lastUpdate);
            }
        }
    } catch(e) {} 
}

function renderizarArvoresEspelhamento() { 
    renderizarArvoreMirror(mirroringState.editableTree, 'mirror-tree-editable', true); 
    renderizarArvoreMirror(mirroringState.syncedTree, 'mirror-tree-synced', false); 
    const treeA = document.getElementById('mirror-tree-editable'), treeB = document.getElementById('mirror-tree-synced');
    if (treeA && treeB) {
        const syncScroll = (e) => { const s = e.target, t = s === treeA ? treeB : treeA; t.removeEventListener('scroll', syncScroll); t.scrollTop = s.scrollTop; t.addEventListener('scroll', syncScroll); };
        treeA.addEventListener('scroll', syncScroll); treeB.addEventListener('scroll', syncScroll);
    }
    const container = document.querySelector('.mirroring-container');
    if (container) { const grid = document.querySelector('.mirror-grid'); if (grid) grid.style.height = `${container.offsetHeight - 80}px`; }
}

function criarNovaPastaMirror() {
    if (!mirroringState.editableTree) return; let target = mirroringState.editableTree;
    if (mirroringState.selectedIds.length > 0) { const n = findMirrorNode(mirroringState.editableTree, mirroringState.selectedIds[0]); if (n) target = n.type === "directory" ? n : findMirrorParent(mirroringState.editableTree, n.id); }
    const id = "m_" + Date.now(); target.isExpanded = true; target.children.push({ id, name: "Nova Pasta", type: "directory", isExpanded: true, file_count: 0, total_file_count: 0, status: "pending", children: [] });
    target.children.sort((a,b) => a.name.localeCompare(b.name, 'pt-BR', { numeric: true })); selecionarItemMirror(id); iniciarRenomeacaoMirror(); persistirMirroringState();
}

function iniciarRenomeacaoMirror() {
    if (mirroringState.selectedIds.length === 0) return; const id = mirroringState.selectedIds[0], n = findMirrorNode(mirroringState.editableTree, id), el = document.querySelector(`#mirror-tree-editable [data-id="${id}"]`);
    if (!n || !el) return; const span = el.querySelector('.folder-name-text') || el.querySelector('.file-name-text') || el.querySelector('span');
    const input = document.createElement('input'); input.type = 'text'; input.className = 'inline-rename-input'; input.value = n.name;
    span.style.display = 'none'; span.parentNode.insertBefore(input, span); 
    setTimeout(() => { input.focus(); if (n.type === "file") { const lastDot = n.name.lastIndexOf('.'); if (lastDot > 0) input.setSelectionRange(0, lastDot); else input.select(); } else input.select(); }, 10);
    const done = (salvar) => { if (salvar && input.value.trim() && input.value.trim() !== n.name) { n.name = input.value.trim(); n.status = "pending"; mirroringState.syncedTree = JSON.parse(JSON.stringify(mirroringState.editableTree)); persistirMirroringState(); } renderizarArvoresEspelhamento(); };
    input.onkeydown = (e) => { if (e.key === 'Enter') done(true); if (e.key === 'Escape') done(false); }; input.onblur = () => done(true);
}

function removerPastaMirror() {
    if (mirroringState.selectedIds.length === 0) return; confirmar("Remover", "Excluir itens?").then(ok => {
        if (ok) {
            mirroringState.selectedIds.forEach(id => { const p = findMirrorParent(mirroringState.editableTree, id); if (p) { const idx = p.children.findIndex(c => c.id === id); p.children.splice(idx, 1); } });
            recalcularContagensVirtuais(mirroringState.editableTree); mirroringState.syncedTree = JSON.parse(JSON.stringify(mirroringState.editableTree)); renderizarArvoresEspelhamento(); persistirMirroringState();
        }
    });
}

function inicializarResizerUnificado() {
    const divider = document.querySelector('.mirror-divider'), gripV = document.querySelector('.resize-handle'), leftPanel = document.getElementById('mirror-panel-left'), rightPanel = document.getElementById('mirror-panel-right'), grid = document.querySelector('.mirror-grid'), mainContainer = document.querySelector('.mirroring-container');
    if (!divider || !gripV || !leftPanel || !rightPanel || !grid || !mainContainer) return;
    let isResizingH = false, isResizingV = false;
    divider.addEventListener('mousedown', (e) => { isResizingH = true; document.body.style.cursor = 'col-resize'; divider.classList.add('active'); e.preventDefault(); });
    gripV.addEventListener('mousedown', (e) => { isResizingV = true; document.body.style.cursor = 'ns-resize'; e.preventDefault(); });
    document.addEventListener('mousemove', (e) => {
        if (isResizingH) { const gridRect = grid.getBoundingClientRect(); let percentage = ((e.clientX - gridRect.left) / gridRect.width) * 100; percentage = Math.max(15, Math.min(85, percentage)); leftPanel.style.flex = 'none'; rightPanel.style.flex = 'none'; leftPanel.style.width = `${percentage}%`; rightPanel.style.width = `${100 - percentage - 1}%`; }
        if (isResizingV) { const containerRect = mainContainer.getBoundingClientRect(); let newHeight = Math.max(400, Math.min(1200, e.clientY - containerRect.top)); mainContainer.style.height = `${newHeight}px`; grid.style.height = `${newHeight - 80}px`; }
    });
    document.addEventListener('mouseup', () => { isResizingH = false; isResizingV = false; document.body.style.cursor = 'default'; divider.classList.remove('active'); });
}

function ativarResizerComSeguranca() { if (document.querySelector('.mirroring-container')) inicializarResizerUnificado(); else setTimeout(ativarResizerComSeguranca, 500); }
document.addEventListener('DOMContentLoaded', ativarResizerComSeguranca);
window.addEventListener('load', ativarResizerComSeguranca);
