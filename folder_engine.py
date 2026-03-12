import os
import re
import json
import shutil

class FolderEngine:
    """
    Motor de Lógica v5.0 - Arquitetura Recursiva Sênior.
    Preserva a hierarquia absoluta de pastas independente da profundidade.
    """
    
    def __init__(self):
        app_data_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'StructureBuilderPro')
        os.makedirs(app_data_dir, exist_ok=True)
        self.templates_file = os.path.join(app_data_dir, "quick_templates.json")
        self.session_file = os.path.join(app_data_dir, "mirror_session.json")

    def _fix_path(self, path):
        """Suporte a caminhos longos e caracteres especiais no Windows."""
        abs_p = os.path.abspath(path)
        if os.name == 'nt' and not abs_p.startswith('\\\\?\\'):
            return '\\\\?\\' + abs_p.replace('/', os.sep)
        return abs_p

    def _sanitize(self, name):
        if not name: return ""
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()

    def load_quick_templates(self):
        if not os.path.exists(self.templates_file): return []
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []

    def save_quick_templates(self, templates):
        with open(self.templates_file, 'w', encoding='utf-8') as f: json.dump(templates, f, indent=4)

    def scan_recursive(self, path, include_files=False):
        """Escaneia o disco com fidelidade total. No modo Espelhamento, não ignora nada para bater com o Windows."""
        fixed_path = self._fix_path(path)
        node = {
            "name": os.path.basename(path),
            "full_path": path,
            "type": "directory",
            "children": [],
            "file_count": 0,
            "total_file_count": 0
        }
        
        # Filtros de exclusão (Apenas para o menu original de templates)
        ignore_set = {
            'venv', '.venv', '__pycache__', 'node_modules', '.git', 
            '.idea', '.vscode', 'build', 'dist', '.gemini', '.pytest_cache'
        }
        
        file_count = 0
        total_file_count = 0
        
        try:
            with os.scandir(fixed_path) as it:
                for entry in it:
                    # Lógica para DIRETÓRIOS
                    if entry.is_dir():
                        # Se NÃO for espelhamento, aplicamos filtros de limpeza visual
                        if not include_files:
                            if entry.name.startswith('.') or entry.name in ignore_set:
                                continue
                        
                        # No espelhamento, entramos em TUDO para garantir a contagem fiel
                        child_node = self.scan_recursive(entry.path, include_files)
                        node["children"].append(child_node)
                        total_file_count += child_node.get("total_file_count", 0)
                    
                    # Lógica para ARQUIVOS
                    elif entry.is_file():
                        # Se não for espelhamento, ignoramos arquivos ocultos/limpeza
                        if not include_files:
                            if entry.name.startswith('.') or entry.name in ignore_set:
                                continue
                            
                        file_count += 1
                        total_file_count += 1
                        
                        # No espelhamento, mantemos os arquivos na estrutura de dados
                        if include_files:
                            node["children"].append({
                                "name": entry.name,
                                "full_path": entry.path,
                                "type": "file",
                                "children": []
                            })
        except (PermissionError, Exception):
            pass # Garante que erro em uma pasta não pare toda a contagem
            
        node["file_count"] = file_count
        node["total_file_count"] = total_file_count
        return node

    def perform_copy(self, source, target):
        """Copia a estrutura completa para um novo local."""
        try:
            if os.path.exists(self._fix_path(target)):
                raise Exception("O destino já existe.")
            shutil.copytree(self._fix_path(source), self._fix_path(target))
            return True
        except Exception as e:
            return str(e)

    def perform_delete_physical(self, path):
        """Deleta fisicamente a estrutura completa."""
        try:
            if os.path.exists(self._fix_path(path)):
                shutil.rmtree(self._fix_path(path))
                return True
            return "Caminho não encontrado."
        except Exception as e:
            return str(e)

    def sync_mirroring(self, base_path, tree_data):
        """
        Aplica as mudanças da árvore virtual no disco físico.
        Move arquivos e pastas e remove o que foi deletado na UI.
        Usa lógica de compensação para renomeações de pastas pai.
        """
        try:
            def process_mirror_node(node, current_physical_parent):
                # O target_path é onde o item DEVE estar agora
                target_path = os.path.join(current_physical_parent, self._sanitize(node["name"]))
                original_path = node.get("full_path")
                
                # Se o item já existe no disco no local correto (target_path), 
                # atualizamos o original_path para evitar tentativas de move inválidas
                if os.path.exists(self._fix_path(target_path)):
                    # Se ele já está lá, ele se torna a nossa nova referência de 'original'
                    original_path = target_path

                # Sincronização de Movimentação/Criação
                if original_path and os.path.exists(self._fix_path(original_path)):
                    # Só move se o local original for diferente do destino final sanitizado
                    if os.path.normcase(os.path.normpath(original_path)) != os.path.normcase(os.path.normpath(target_path)):
                        try:
                            os.makedirs(self._fix_path(os.path.dirname(target_path)), exist_ok=True)
                            # Se for diretório, usamos move que lida com a árvore inteira
                            # Se o destino já existir como diretório, shutil.move pode falhar ou aninhar.
                            # Precisamos ser cirúrgicos.
                            if os.path.isdir(self._fix_path(original_path)):
                                # Se o destino já existe (talvez uma pasta vazia criada por engano), removemos antes de mover
                                if os.path.exists(self._fix_path(target_path)) and os.path.isdir(self._fix_path(target_path)):
                                    # Se a pasta destino existe e está vazia ou é diferente, removemos para o move fluir
                                    if not os.listdir(self._fix_path(target_path)):
                                        os.rmdir(self._fix_path(target_path))
                                    else:
                                        # Caso complexo: Merge de pastas? Não, o move deve ser soberano.
                                        # Para segurança, tentaremos o move direto.
                                        pass
                            
                            shutil.move(self._fix_path(original_path), self._fix_path(target_path))
                            # ATENÇÃO: Após o move, o original_path agora é o target_path
                            original_path = target_path
                        except PermissionError:
                            raise Exception(f"Acesso Negado: {node['name']}. O item está em uso.")
                else:
                    # Se não existe e é diretório, cria
                    if node["type"] == "directory":
                        os.makedirs(self._fix_path(target_path), exist_ok=True)
                        original_path = target_path

                # Identifica o que deve ser mantido neste nível
                keep_in_disk = set()
                if node["type"] == "directory":
                    # Primeiro, processamos todos os filhos para garantir que eles sejam movidos/criados
                    for child in node.get("children", []):
                        # Importante: O original_path do filho pode precisar ser atualizado 
                        # se o pai foi movido. Mas o shutil.move já levou os filhos junto fisicamente.
                        # Por isso, o process_mirror_node agora verifica se o filho já existe no target_path.
                        
                        # Se o pai mudou (original_path foi movido para target_path), 
                        # os filhos físicos também mudaram. Atualizamos a referência do filho se necessário.
                        if original_path != node.get("full_path"):
                            # Se o pai mudou, tentamos deduzir o novo local do filho para o original_path dele
                            if child.get("full_path"):
                                # Pega o nome relativo do filho e junta com o novo caminho do pai
                                rel_name = os.path.basename(child["full_path"])
                                child["full_path"] = os.path.join(original_path, rel_name)

                        keep_in_disk.add(self._sanitize(child["name"]))
                        process_mirror_node(child, target_path)

                    # Engenharia Sênior: Remoção da deleção automática baseada em varredura de disco.
                    # No sistema de espelhamento, priorizamos a segurança e a integridade total dos arquivos.
                    # A sincronização deve apenas criar, mover ou renomear. 
                    # Arquivos físicos que não constam na árvore virtual são preservados, evitando exclusões acidentais.
                    pass

            # Executa a sincronização
            process_mirror_node(tree_data, os.path.dirname(base_path))
            
            # Recalcula o novo base_path caso a raiz tenha sido renomeada
            new_base_path = os.path.join(os.path.dirname(base_path), self._sanitize(tree_data["name"]))
            return {"status": "success", "new_structure": self.scan_recursive(new_base_path, include_files=True)}
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return {"error": str(e)}


    def save_session_state(self, data):
        """Salva o estado da sessão de espelhamento de forma ultra-rápida (Compacto)."""
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                # Removido indent para máxima performance de escrita
                json.dump(data, f, ensure_ascii=False)
            return True
        except Exception as e:
            return str(e)

    def load_session_state(self):
        """Carrega o estado da sessão de espelhamento do diretório AppData."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        except Exception:
            return None

    def load_existing_structure(self, path, include_files=False):
        """Carrega uma estrutura do disco, opcionalmente incluindo arquivos."""
        if not os.path.isdir(path): raise Exception("Pasta não encontrada.")
        full_tree = self.scan_recursive(path, include_files)
        return {
            "base_dir": os.path.dirname(path),
            "main_folder": full_tree["name"],
            "main_folder_path": path,
            "tree_structure": full_tree
        }

    def scan_physical_structure(self, path):
        """Escaneia o disco e retorna um modelo pronto para a biblioteca."""
        if not os.path.isdir(path):
            raise Exception("Caminho inválido para escaneamento.")
        
        full_tree = self.scan_recursive(path)
        return {
            "main_folder": full_tree["name"],
            "tree_structure": full_tree
        }

    def perform_creation(self, base_dir, main_name, tree_data):
        """Cria uma nova estrutura do zero usando os dados da árvore."""
        res = self.sincronizar_master(base_dir, main_name, tree_data, is_existing=False)
        if "error" in res: raise Exception(res["error"])
        return res["path"]

    def perform_update(self, main_name, original_state, tree_data):
        """Simula a atualização e retorna o que deve ser removido."""
        # Na v5.0, a sincronização é direta, mas mantemos o contrato para a ponte.
        res = self.sincronizar_master(None, main_name, tree_data, original_state, is_existing=True)
        if "error" in res: raise Exception(res["error"])
        return {
            "status": "success",
            "effective_path": res["path"],
            "removed_folders": [], # A sincronização master já cuidou disso
            "fresh_data": res["fresh_data"]
        }

    def finalize_removals(self, paths):
        """Método de compatibilidade para finalizar remoções (já feitas no master)."""
        return True

    def sincronizar_master(self, base_dir, main_name, recursive_tree, original_state=None, is_existing=False):
        """
        SINCRONIZADOR HIERÁRQUICO:
        Percorre a árvore recursiva e replica no Windows Explorer.
        """
        try:
            clean_main = self._sanitize(main_name)
            
            # 1. Determinar Raiz
            if is_existing and original_state:
                old_root = original_state["main_folder_path"]
                target_root = os.path.join(os.path.dirname(old_root), clean_main)
                if os.path.normpath(old_root) != os.path.normpath(target_root):
                    if os.path.exists(target_root): return {"error": "A pasta já existe no destino."}
                    os.rename(self._fix_path(old_root), self._fix_path(target_root))
            else:
                if not base_dir: return {"error": "Selecione o Diretório Base."}
                target_root = os.path.join(base_dir, clean_main)
                os.makedirs(self._fix_path(target_root), exist_ok=True)

            # 2. Sincronização Recursiva de Subpastas
            def process_node(node, current_physical_parent, is_root_node=False):
                # Para o nó raiz, usamos o nome confirmado pelo usuário no campo de texto
                # Para subpastas, usamos o nome definido no objeto da árvore
                sanitized_name = clean_main if is_root_node else self._sanitize(node["name"])
                meu_caminho = os.path.join(current_physical_parent, sanitized_name)
                os.makedirs(self._fix_path(meu_caminho), exist_ok=True)
                
                # Coleta caminhos reais para identificar o que sobrou no disco (para deleção)
                no_disco = set()
                try:
                    no_disco = {d for d in os.listdir(self._fix_path(meu_caminho)) if os.path.isdir(os.path.join(self._fix_path(meu_caminho), d))}
                except: pass
                
                na_arvore = {self._sanitize(child["name"]) for child in node["children"]}
                
                # Deleção Fiel: Se está no disco mas não na árvore visual, remove.
                if is_existing:
                    for d in no_disco:
                        if d not in na_arvore:
                            path_to_del = os.path.join(meu_caminho, d)
                            shutil.rmtree(self._fix_path(path_to_del))

                # Recursão para os filhos
                for child in node["children"]:
                    process_node(child, meu_caminho, is_root_node=False)

            process_node(recursive_tree, os.path.dirname(target_root), is_root_node=True)

            return {
                "status": "success",
                "path": target_root,
                "fresh_data": self.load_existing_structure(target_root)
            }
        except Exception as e:
            return {"error": str(e)}
