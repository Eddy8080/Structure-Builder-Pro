/**
 * Script Principal de Interface v5.2 - Backup e Restauração
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
});

function sincronizarCamposDaTela() {
    state.mainFolder = document.getElementById('main-folder').value.trim();
    state.baseDir = document.getElementById('base-dir').value.trim();
    // Garante que o nome na árvore esteja sincronizado com o campo de texto
    if (state.tree && state.mainFolder) {
        state.tree.name = state.mainFolder;
    }
}

function inicializarTema() {
    const theme = localStorage.getItem('app-theme') || 'dark';
    if (theme === 'light') { document.body.classList.add('light-theme'); atualizarIconeTema('sun'); }
    document.getElementById('btn-theme-toggle').onclick = () => {
        const isLight = document.body.classList.toggle('light-theme');
        localStorage.setItem('app-theme', isLight ? 'light' : 'dark');
        atualizarIconeTema(isLight ? 'sun' : 'moon');
        Swal.update({ background: isLight ? '#ffffff' : '#1e293b', color: isLight ? '#1e293b' : '#f1f5f9' });
    };
}

function atualizarIconeTema(iconName) {
    const icon = document.getElementById('theme-icon');
    icon.setAttribute('data-lucide', iconName);
    lucide.createIcons();
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
        
        // Pergunta o nome da pasta raiz (desacoplado do modelo) para preservar o original
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
            // Utilizamos o nome customizado no parâmetro main_folder da sincronização
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
    
    // Atualização em tempo real do nome da pasta raiz enquanto digita
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
        if (e.key === 'Escape') document.querySelectorAll('.context-menu, .overlay, .rename-bar').forEach(el => el.classList.add('hidden'));
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

// --- GESTÃO RECURSIVA ---

function buscarNode(node, id) {
    if (node.id === id) return node;
    for (let child of node.children) {
        const found = buscarNode(child, id);
        if (found) return found;
    }
    return null;
}

// Função global de ordenação (Sequência Numérica + Ordem Alfabética)
function compararPastas(a, b) {
    return a.name.localeCompare(b.name, 'pt-BR', { numeric: true, sensitivity: 'base' });
}

function criarNovaPasta() {
    if (!state.tree) return alertar("Aviso", "Defina a Pasta Principal.", 'warning');
    let targetParent = state.tree;
    if (state.selectedId) targetParent = buscarNode(state.tree, state.selectedId);

    const newId = "id_" + Date.now();
    targetParent.isExpanded = true;
    targetParent.children.push({ id: newId, name: "Nova Pasta", isExpanded: true, children: [] });
    targetParent.children.sort(compararPastas);

    renderizarArvore();
    selecionarItem(newId);
    iniciarRenomeacao();
}

function removerPasta(id) {
    if (id === "root") return;
    const deletarRecursivo = (node) => {
        const idx = node.children.findIndex(c => c.id === id);
        if (idx !== -1) { node.children.splice(idx, 1); return true; }
        for (let child of node.children) { if (deletarRecursivo(child)) return true; }
        return false;
    };
    confirmar("Remover", "Deletar esta pasta?").then(ok => {
        if (ok) { 
            deletarRecursivo(state.tree); 
            state.selectedId = null; 
            renderizarArvore(); 
        }
    });
}

function renderizarArvore() {
    const container = document.getElementById('tree-container');
    container.innerHTML = '';
    if (!state.tree) { container.innerHTML = '<div class="empty-tree-state"><p>Estrutura vazia.</p></div>'; return; }

    const montarHTML = (node, isRoot = false) => {
        const divNode = document.createElement('div');
        divNode.className = "tree-node";
        const content = document.createElement('div');
        content.className = `tree-item-content ${state.selectedId === node.id ? 'selected' : ''}`;
        content.dataset.id = node.id;
        const hasChildren = node.children && node.children.length > 0;
        const toggleIcon = hasChildren ? `<i data-lucide="chevron-right" class="toggle-icon ${node.isExpanded ? 'expanded' : ''}" onclick="event.stopPropagation(); togglePasta('${node.id}')"></i>` : `<span class="toggle-placeholder"></span>`;
        const iconType = isRoot ? 'folder-tree' : 'folder';
        content.innerHTML = `${toggleIcon}<i data-lucide="${iconType}" class="folder-icon"></i><span>${node.name}</span>`;
        content.onclick = (e) => { e.stopPropagation(); selecionarItem(node.id); };
        content.ondblclick = (e) => { e.stopPropagation(); togglePasta(node.id); };
        divNode.appendChild(content);

        if (hasChildren) {
            const divChildren = document.createElement('div');
            divChildren.className = "tree-children";
            if (!node.isExpanded) divChildren.classList.add('collapsed');
            
            // Ordenação garantida em cada nível
            node.children.sort(compararPastas);
            
            node.children.forEach(child => divChildren.appendChild(montarHTML(child)));
            divNode.appendChild(divChildren);
        }
        return divNode;
    };
    container.appendChild(montarHTML(state.tree, true));
    lucide.createIcons();
}

function togglePasta(id) {
    const node = buscarNode(state.tree, id);
    if (node) { node.isExpanded = !node.isExpanded; renderizarArvore(); }
}

async function executarAcaoFinal() {
    sincronizarCamposDaTela();
    document.getElementById('btn-apply').click();
    setTimeout(() => { if (!document.querySelector('.swal2-shown')) resetarUI(); }, 1500);
}

// Variável de controle para renomeação segura
let renamingTargetId = null;

function aplicarDadosAoEstado(dados) {
    state.mainFolder = dados.main_folder || "";
    state.originalState = dados;
    document.getElementById('base-dir').value = dados.base_dir || "";
    document.getElementById('main-folder').value = state.mainFolder;
    
    if (dados.tree_structure) {
        state.tree = prepararArvoreRecursiva(dados.tree_structure);
        state.tree.id = "root"; // Garante ID da raiz
        state.tree.isExpanded = true; // Garante que a raiz sempre inicie expandida para visualização
    }
    renderizarArvore();
}

function prepararArvoreRecursiva(node) {
    const newNode = {
        id: node.id || "id_" + Math.random().toString(36).substr(2, 9),
        name: node.name,
        // Engenharia Sênior: Alterado o fallback de true para false para iniciar recolhido
        isExpanded: node.isExpanded !== undefined ? node.isExpanded : false,
        children: (node.children || []).map(c => prepararArvoreRecursiva(c))
    };

    newNode.children.sort(compararPastas);
    return newNode;
}

function atualizarUIModo(isUpdate) {
    const editMode = isUpdate || state.isEditingTemplate;
    document.getElementById('btn-create').classList.toggle('hidden', editMode);
    document.getElementById('btn-update').classList.toggle('hidden', !editMode);
    document.getElementById('btn-apply-template').classList.toggle('hidden', !state.isEditingTemplate);
}

function resetarUI() {
    state = { baseDir: "", mainFolder: "", tree: null, selectedId: null, selectedTemplateIdx: null, originalState: null, isExistingStructure: false, isEditingTemplate: false };
    document.getElementById('base-dir').value = "";
    document.getElementById('main-folder').value = "";
    atualizarUIModo(false);
    renderizarArvore();
}

function iniciarRenomeacao() {
    const bar = document.getElementById('rename-floating-bar');
    const input = document.getElementById('rename-input');
    const node = buscarNode(state.tree, state.selectedId);
    
    if (node) {
        renamingTargetId = node.id; // Trava o ID para edição
        bar.classList.remove('hidden');
        input.value = node.name;
        setTimeout(() => { input.focus(); input.select(); }, 10);
    }
    document.getElementById('btn-confirm-rename').onclick = confirmarRenomeacao;
}

function confirmarRenomeacao() {
    const input = document.getElementById('rename-input');
    const novoNome = input.value.trim();
    
    if (renamingTargetId && novoNome !== "") {
        const node = buscarNode(state.tree, renamingTargetId);
        if (node) {
            node.name = novoNome;
            // Se for a raiz, sincroniza com o input de Pasta Principal
            if (node.id === "root") {
                state.mainFolder = node.name;
                document.getElementById('main-folder').value = node.name;
            }
        }
    }
    
    renamingTargetId = null;
    document.getElementById('rename-floating-bar').classList.add('hidden');
    renderizarArvore();
}

function selecionarItem(id) { state.selectedId = id; renderizarArvore(); }

async function carregarModelos() {
    const modelos = await eel.obter_modelos_rapidos()();
    const list = document.getElementById('templates-list');
    list.innerHTML = '';
    modelos.forEach((m, idx) => {
        const item = document.createElement('div');
        item.className = 'template-item';
        if (state.selectedTemplateIdx === idx) item.classList.add('selected');
        item.innerHTML = `<i data-lucide="folder"></i> <span>${m.main_folder}</span>`;
        item.onclick = (e) => { 
            e.stopPropagation(); state.selectedTemplateIdx = idx; state.selectedId = null; 
            state.isExistingStructure = false; state.isEditingTemplate = true; 
            document.querySelectorAll('.template-item').forEach(el => el.classList.remove('selected')); 
            item.classList.add('selected'); aplicarModelo(m); atualizarUIModo(true);
        };
        item.oncontextmenu = (e) => { e.preventDefault(); e.stopPropagation(); state.selectedTemplateIdx = idx; document.querySelectorAll('.template-item').forEach(el => el.classList.remove('selected')); item.classList.add('selected'); mostrarMenuModelo(e, idx); };
        list.appendChild(item);
    });
    lucide.createIcons();
}

function mostrarMenuModelo(e, index) {
    const menu = document.getElementById('template-context-menu');
    menu.style.top = `${e.clientY}px`; menu.style.left = `${e.clientX}px`;
    menu.classList.remove('hidden');
    document.getElementById('tm-rename').onclick = () => renomearModeloInterface(index);
    document.getElementById('tm-delete').onclick = () => removerModeloInterface(index);
}

async function renomearModeloInterface(index) {
    const modelos = await eel.obter_modelos_rapidos()();
    const { value: novoNome } = await Swal.fire({ title: 'Renomear', input: 'text', inputValue: modelos[index].main_folder, showCancelButton: true, confirmButtonColor: '#3b82f6', background: document.body.classList.contains('light-theme') ? '#ffffff' : '#1e293b', color: document.body.classList.contains('light-theme') ? '#1e293b' : '#f1f5f9' });
    
    if (novoNome && novoNome.trim() !== "") { 
        const nomeFinal = novoNome.trim();
        await eel.renomear_modelo_rapido(index, nomeFinal)(); 
        
        // Se o modelo renomeado for o que está sendo editado, atualiza o estado
        if (state.selectedTemplateIdx === index) {
            state.mainFolder = nomeFinal;
            document.getElementById('main-folder').value = nomeFinal;
            if (state.tree) {
                state.tree.name = nomeFinal;
                renderizarArvore();
            }
        }
        
        carregarModelos(); 
    }
}

async function removerModeloInterface(index) { if (await confirmar("Remover", "Remover este modelo?")) { await eel.remover_modelo_rapido(index)(); state.selectedTemplateIdx = null; carregarModelos(); } }

function aplicarModelo(modelo) { aplicarDadosAoEstado(modelo); }

function configurarMenuContexto() {
    const menu = document.getElementById('context-menu');
    document.getElementById('tree-container').oncontextmenu = (e) => {
        e.preventDefault();
        const itemElement = e.target.closest('.tree-item-content');
        if (itemElement) selecionarItem(itemElement.dataset.id);
        else { state.selectedId = null; renderizarArvore(); }
        menu.style.top = `${e.clientY}px`; menu.style.left = `${e.clientX}px`;
        menu.classList.remove('hidden');
    };
    document.getElementById('cm-new').onclick = () => criarNovaPasta();
    document.getElementById('cm-rename').onclick = () => iniciarRenomeacao();
    document.getElementById('cm-delete').onclick = () => removerPasta(state.selectedId);
}

function mostrarLoader(msg) { document.getElementById('loader-message').innerText = msg; document.getElementById('loader-overlay').classList.remove('hidden'); }
function esconderLoader() { document.getElementById('loader-overlay').classList.add('hidden'); }

async function gerarDiagrama() {
    if (!state.tree) return;
    const modal = document.getElementById('diagram-modal');
    const container = document.getElementById('mermaid-container');
    modal.classList.remove('hidden');
    container.innerHTML = '<div class="spinner"></div>';
    mermaid.initialize({ startOnLoad: false, theme: document.body.classList.contains('light-theme') ? 'default' : 'dark', securityLevel: 'loose' });
    let mermaidText = "graph LR\n";
    mermaidText += "classDef root fill:#3b82f6,stroke:#2563eb,color:#fff,stroke-width:2px;\n";
    mermaidText += "classDef folder fill:#1e293b,stroke:#3b82f6,color:#f1f5f9;\n";
    const processNode = (node, isRoot = false) => {
        const id = node.id.replace(/-/g, "_");
        const name = `"${node.name.replace(/"/g, "'")}"`;
        mermaidText += `  ${id}[${name}]\n`;
        mermaidText += `  class ${id} ${isRoot ? 'root' : 'folder'}\n`;
        node.children.forEach(child => {
            const childId = child.id.replace(/-/g, "_");
            mermaidText += `  ${id} --> ${childId}\n`;
            processNode(child);
        });
    };
    processNode(state.tree, true);
    try { const { svg } = await mermaid.render('mermaid-svg', mermaidText); container.innerHTML = svg; }
    catch (error) { console.error("Erro Mermaid:", error); container.innerHTML = `<p style="color:red">Erro visual.</p>`; }
}

function baixarDiagramaSvg() {
    const svgElement = document.querySelector('#mermaid-container svg');
    if (!svgElement) return;
    const downloadLink = document.createElement("a");
    downloadLink.href = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svgElement)], { type: "image/svg+xml;charset=utf-8" }));
    downloadLink.download = `${state.mainFolder || 'estrutura'}_diagrama.svg`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}
