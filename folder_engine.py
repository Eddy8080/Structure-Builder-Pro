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

    def scan_recursive(self, path):
        """Escaneia o disco e gera um objeto hierárquico fiel."""
        fixed_path = self._fix_path(path)
        node = {
            "name": os.path.basename(path),
            "full_path": path,
            "children": []
        }
        
        try:
            # Lista apenas diretórios, ignorando ocultos e sistema
            items = [d for d in os.listdir(fixed_path) if os.path.isdir(os.path.join(fixed_path, d))]
            items = [d for d in items if not d.startswith('.') and d not in {'venv', '__pycache__', 'node_modules'}]
            
            for item in items:
                child_path = os.path.join(path, item)
                node["children"].append(self.scan_recursive(child_path))
        except:
            pass
            
        return node

    def load_existing_structure(self, path):
        if not os.path.isdir(path): raise Exception("Pasta não encontrada.")
        full_tree = self.scan_recursive(path)
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
