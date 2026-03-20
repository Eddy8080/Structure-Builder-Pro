import os
import sys
import re
import json
import shutil
import subprocess

class FolderEngine:
    """
    Engine v3.11 - Desacoplado v5.6.2.
    Arquitetura Recursiva Sênior com Blindagem de Escopo e Assinatura Heurística.
    """
    
    def __init__(self):
        # Engenharia Sênior: Identificação da "Home" e Modo de Execução
        if getattr(sys, 'frozen', False):
            self.app_home = os.path.normpath(os.path.dirname(sys.executable))
            self.is_dev = False
        else:
            self.app_home = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
            self.is_dev = True

        # Proteção 1: Isolamento de AppData (Evita compartilhamento de templates entre Dev e Prod)
        suffix = "_DEV" if self.is_dev else ""
        self.app_data_dir = os.path.normpath(os.path.join(
            os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 
            f'StructureBuilderPro{suffix}'
        ))
        
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.templates_file = os.path.join(self.app_data_dir, "quick_templates.json")
        self.session_file = os.path.join(self.app_data_dir, "mirror_session.json")
        
        print(f"[SHIELD] Modo: {'DESENVOLVIMENTO' if self.is_dev else 'PRODUÇÃO'}")
        print(f"[SHIELD] AppData Isolado: {self.app_data_dir}")

    def _is_protected_path(self, path):
        """
        Verificação de Segurança Multinível:
        1. Proteção por Caminho Absoluto (Home e AppData).
        2. Proteção por Assinatura (Impede mexer em QUALQUER pasta que pareça ser o projeto).
        """
        if not path: return False
        
        # Normaliza o caminho para comparação absoluta
        target = os.path.normcase(os.path.normpath(os.path.abspath(path)))
        home = os.path.normcase(self.app_home)
        data = os.path.normcase(self.app_data_dir)

        # 1. Trava de Home/AppData (Contexto Atual)
        if target == home or target.startswith(home + os.sep):
            return True
            
        if target == data or target.startswith(data + os.sep):
            return True

        # 2. Trava por Assinatura (Heurística)
        # Se a pasta contém arquivos vitais do código-fonte, ela é considerada PROTEGIDA.
        signature_files = ['bridge.py', 'folder_engine.py', 'version_control.py', 'installer_config.iss']
        if os.path.isdir(target):
            for sig in signature_files:
                if os.path.exists(os.path.join(target, sig)):
                    return True
        
        # 3. Trava de Pastas de Sistema Críticas
        system_folders = [
            os.path.normcase(os.environ.get('SystemRoot', 'C:\\Windows')),
            os.path.normcase(os.environ.get('ProgramFiles', 'C:\\Program Files')),
            os.path.normcase(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'))
        ]
        for sys_f in system_folders:
            if target == sys_f or target.startswith(sys_f + os.sep):
                if not target.startswith(home):
                    return True

        return False

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
        """Escaneia o disco. Proteção Sênior: Bloqueia pastas de infraestrutura de código."""
        # Remove prefixo \\?\ do caminho para garantir full_path consistente em toda a árvore.
        # os.scandir retorna entry.path com o mesmo prefixo do path passado — sem normalizar,
        # filhos e netos ficam com \\?\C:\... enquanto a raiz fica com C:\..., quebrando
        # comparações de prefixo em substituir_prefixo_recursivo durante o espelhamento.
        if isinstance(path, str) and path.startswith('\\\\?\\'):
            path = path[4:]
        fixed_path = self._fix_path(path)
        node = {
            "name": os.path.basename(path),
            "full_path": path,
            "type": "directory",
            "children": [],
            "file_count": 0,
            "total_file_count": 0
        }

        # Filtros de exclusão UNIVERSAIS (Nunca devem ser espelhados ou contados)
        # Isso remove o risco de replicar venv ou .git para dentro de pastas de trabalho.
        ignore_set = {
            'venv', '.venv', '__pycache__', 'node_modules', '.git',
            '.idea', '.vscode', 'build', 'dist', '.gemini', '.pytest_cache',
            'output_installer', 'TESTE_VALIDACAO_ESPELHAMENTO', 'venv_PROD'
        }

        file_count = 0
        total_file_count = 0

        try:
            with os.scandir(fixed_path) as it:
                for entry in it:
                    # Lógica de Exclusão Blindada (Independente de ser espelhamento ou não)
                    if entry.name.startswith('.') or entry.name in ignore_set:
                        continue

                    if entry.is_dir():
                        # Usa path normalizado (sem \\?\) para manter full_path consistente
                        child_path = os.path.join(path, entry.name)
                        child_node = self.scan_recursive(child_path, include_files)
                        node["children"].append(child_node)
                        total_file_count += child_node.get("total_file_count", 0)

                    elif entry.is_file():
                        file_count += 1
                        total_file_count += 1

                        if include_files:
                            node["children"].append({
                                "name": entry.name,
                                "full_path": os.path.join(path, entry.name),
                                "type": "file",
                                "children": []
                            })
        except (PermissionError, Exception):
            pass

        node["file_count"] = file_count
        node["total_file_count"] = total_file_count
        return node

    def perform_copy(self, source, target):
        """Copia a estrutura completa para um novo local com Blindagem."""
        try:
            if self._is_protected_path(target):
                raise Exception("Operação Bloqueada: O destino é uma Zona Protegida do Sistema/Projeto.")
            
            if os.path.exists(self._fix_path(target)):
                raise Exception("O destino já existe.")
            shutil.copytree(self._fix_path(source), self._fix_path(target))
            return True
        except Exception as e:
            return str(e)

    def perform_delete_physical(self, path):
        """Deleta fisicamente a estrutura completa com Blindagem."""
        try:
            if self._is_protected_path(path):
                raise Exception("Operação Bloqueada: Impossível deletar Zona Protegida do Sistema/Projeto.")
            
            if os.path.exists(self._fix_path(path)):
                shutil.rmtree(self._fix_path(path))
                return True
            return "Caminho não encontrado."
        except Exception as e:
            return str(e)

    def _mover_para_lixeira(self, path):
        """Envia arquivo ou pasta para a Lixeira do Windows via Microsoft.VisualBasic."""
        try:
            abs_path = os.path.abspath(path)
            if not os.path.exists(self._fix_path(abs_path)):
                return True
            if os.path.isdir(abs_path):
                ps_cmd = (
                    'Add-Type -AssemblyName Microsoft.VisualBasic; '
                    f'[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory('
                    f'"{abs_path}", "OnlyErrorDialogs", "SendToRecycleBin")'
                )
            else:
                ps_cmd = (
                    'Add-Type -AssemblyName Microsoft.VisualBasic; '
                    f'[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('
                    f'"{abs_path}", "OnlyErrorDialogs", "SendToRecycleBin")'
                )
            subprocess.run(
                ['powershell', '-WindowStyle', 'Hidden', '-NonInteractive', '-Command', ps_cmd],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except Exception as e:
            return str(e)

    def sync_mirroring(self, base_path, tree_data):
        """
        Aplica as mudanças da árvore virtual no disco físico com Blindagem de Escopo.
        """
        try:
            # Trava de Segurança na Raiz
            if self._is_protected_path(base_path):
                raise Exception("Operação de Espelhamento Bloqueada: A pasta alvo é uma Zona Protegida.")

            def substituir_prefixo_recursivo(no, prefixo_antigo, prefixo_novo):
                if no.get("full_path"):
                    # Remove prefixo \\?\ de sessões antigas antes de comparar
                    fp = no["full_path"]
                    if isinstance(fp, str) and fp.startswith('\\\\?\\'):
                        fp = fp[4:]
                    ant = os.path.normcase(os.path.normpath(prefixo_antigo))
                    atual = os.path.normcase(os.path.normpath(fp))
                    if atual.startswith(ant + os.sep) or atual == ant:
                        rel = os.path.relpath(
                            os.path.normpath(fp),
                            os.path.normpath(prefixo_antigo)
                        )
                        no["full_path"] = os.path.join(prefixo_novo, rel)
                for filho in no.get("children", []):
                    substituir_prefixo_recursivo(filho, prefixo_antigo, prefixo_novo)

            def normalizar_path(p):
                r"""Remove prefixo \\?\ e normaliza separadores para comparações."""
                if isinstance(p, str) and p.startswith('\\\\?\\'):
                    p = p[4:]
                return p

            def resolver_original(full_path_raw, current_physical_parent):
                """
                Resolve o caminho físico real de um item com base em duas estratégias:
                1. full_path direto (após normalizar UNC)
                2. Fallback: procura pelo nome original do item dentro do diretório
                   físico atual — cobre o caso em que a pasta pai foi renomeada mas
                   substituir_prefixo_recursivo não atualizou este nó por qualquer motivo.
                """
                p = normalizar_path(full_path_raw)
                if p and os.path.exists(self._fix_path(p)):
                    return p
                # Fallback: o item pode ter sido arrastado junto com o pai renomeado
                if p:
                    candidato = os.path.join(current_physical_parent, os.path.basename(p))
                    if os.path.exists(self._fix_path(candidato)):
                        return candidato
                return None

            def process_mirror_node(node, current_physical_parent):
                # Itens marcados para deletar — envia para a Lixeira e não processa filhos
                if node.get("status") == "to_delete":
                    original_path = resolver_original(
                        node.get("full_path"), current_physical_parent
                    )
                    if original_path and os.path.exists(self._fix_path(original_path)):
                        self._mover_para_lixeira(original_path)
                    return

                # O target_path é onde o item DEVE estar agora
                target_path = os.path.join(current_physical_parent, self._sanitize(node["name"]))

                # Blindagem interna recursiva
                if self._is_protected_path(target_path):
                    raise Exception(f"Violação de Escopo: Tentativa de escrita em zona protegida: {target_path}")

                # Resolve o caminho físico real do item (direto ou via fallback por nome)
                original_path = resolver_original(node.get("full_path"), current_physical_parent)

                # Se o item já existe no disco no local correto (target_path),
                # atualizamos o original_path para evitar tentativas de move inválidas
                if os.path.exists(self._fix_path(target_path)):
                    original_path = target_path

                # Sincronização de Movimentação/Criação
                if original_path and os.path.exists(self._fix_path(original_path)):
                    # Só move se o local original for diferente do destino final sanitizado
                    if os.path.normcase(os.path.normpath(original_path)) != os.path.normcase(os.path.normpath(target_path)):
                        try:
                            os.makedirs(self._fix_path(os.path.dirname(target_path)), exist_ok=True)
                            if os.path.isdir(self._fix_path(original_path)):
                                if os.path.exists(self._fix_path(target_path)) and os.path.isdir(self._fix_path(target_path)):
                                    if not os.listdir(self._fix_path(target_path)):
                                        os.rmdir(self._fix_path(target_path))
                            shutil.move(self._fix_path(original_path), self._fix_path(target_path))
                            original_path = target_path
                        except PermissionError:
                            raise Exception(f"Acesso Negado: {node['name']}. O item está em uso.")
                        except Exception as e:
                            raise Exception(f"Erro ao mover {node['name']}: {str(e)}")
                else:
                    # Se não existe e é diretório, cria
                    if node["type"] == "directory":
                        os.makedirs(self._fix_path(target_path), exist_ok=True)
                        original_path = target_path

                # Processa descendentes de diretórios
                if node["type"] == "directory":
                    old_full = normalizar_path(node.get("full_path", ""))
                    if (original_path and old_full and
                            os.path.normcase(os.path.normpath(original_path)) !=
                            os.path.normcase(os.path.normpath(old_full))):
                        for child in node.get("children", []):
                            substituir_prefixo_recursivo(child, old_full, original_path)
                    for child in node.get("children", []):
                        process_mirror_node(child, target_path)

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
        """Salva o estado da sessão de espelhamento de forma ultra-rápica."""
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            return True
        except Exception as e:
            return str(e)

    def load_session_state(self):
        """Carrega o estado da sessão de espelhamento."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        except Exception:
            return None

    def load_existing_structure(self, path, include_files=False):
        """Carrega uma estrutura do disco."""
        if not os.path.isdir(path): raise Exception("Pasta não encontrada.")
        full_tree = self.scan_recursive(path, include_files)
        return {
            "base_dir": os.path.dirname(path),
            "main_folder": full_tree["name"],
            "main_folder_path": path,
            "tree_structure": full_tree
        }

    def scan_physical_structure(self, path):
        """Escaneia o disco."""
        if not os.path.isdir(path):
            raise Exception("Caminho inválido.")
        full_tree = self.scan_recursive(path)
        return {
            "main_folder": full_tree["name"],
            "tree_structure": full_tree
        }

    def perform_creation(self, base_dir, main_name, tree_data):
        """Cria uma nova estrutura."""
        res = self.sincronizar_master(base_dir, main_name, tree_data, is_existing=False)
        if "error" in res: raise Exception(res["error"])
        return res["path"]

    def perform_update(self, main_name, original_state, tree_data):
        """Simula a atualização."""
        res = self.sincronizar_master(None, main_name, tree_data, original_state, is_existing=True)
        if "error" in res: raise Exception(res["error"])
        return {
            "status": "success",
            "effective_path": res["path"],
            "removed_folders": [], 
            "fresh_data": res["fresh_data"]
        }

    def finalize_removals(self, paths):
        """Finaliza remoções."""
        return True

    def sincronizar_master(self, base_dir, main_name, recursive_tree, original_state=None, is_existing=False):
        """SINCRONIZADOR HIERÁRQUICO com Blindagem de Escopo."""
        try:
            clean_main = self._sanitize(main_name)
            if is_existing and original_state:
                old_root = original_state["main_folder_path"]
                target_root = os.path.join(os.path.dirname(old_root), clean_main)
                
                # Blindagem na Atualização
                if self._is_protected_path(target_root):
                    raise Exception("Operação Bloqueada: A pasta alvo de atualização é uma Zona Protegida.")

                if os.path.normpath(old_root) != os.path.normpath(target_root):
                    if os.path.exists(target_root): return {"error": "A pasta já existe no destino."}
                    os.rename(self._fix_path(old_root), self._fix_path(target_root))
            else:
                if not base_dir: return {"error": "Selecione o Diretório Base."}
                target_root = os.path.join(base_dir, clean_main)
                
                # Blindagem na Criação Nova
                if self._is_protected_path(target_root):
                    raise Exception("Operação Bloqueada: O local de criação é uma Zona Protegida.")

                os.makedirs(self._fix_path(target_root), exist_ok=True)

            def process_node(node, current_physical_parent, is_root_node=False):
                sanitized_name = clean_main if is_root_node else self._sanitize(node["name"])
                meu_caminho = os.path.join(current_physical_parent, sanitized_name)
                
                # Blindagem recursiva profunda
                if self._is_protected_path(meu_caminho):
                    raise Exception(f"Violação de Escopo: Tentativa de escrita em zona protegida: {meu_caminho}")

                os.makedirs(self._fix_path(meu_caminho), exist_ok=True)
                no_disco = set()
                try:
                    no_disco = {d for d in os.listdir(self._fix_path(meu_caminho)) if os.path.isdir(os.path.join(self._fix_path(meu_caminho), d))}
                except: pass
                na_arvore = {self._sanitize(child["name"]) for child in node["children"]}
                if is_existing:
                    for d in no_disco:
                        if d not in na_arvore:
                            path_to_del = os.path.join(meu_caminho, d)
                            
                            # Proteção extra antes de deletar
                            if not self._is_protected_path(path_to_del):
                                shutil.rmtree(self._fix_path(path_to_del))
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
