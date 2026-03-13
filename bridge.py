import ctypes
import os
import sys

# Identificador único para a barra de tarefas do Windows (AppUserModelID)
# Deve ser definido o mais cedo possível para que o ícone seja associado corretamente
myappid = 'google.structure.builder.pro.2.0' 
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

import eel
import tkinter as tk
from tkinter import filedialog
import subprocess
import json
import signal 
import webbrowser
from folder_engine import FolderEngine
from version_control import VersionManager

# Inicializa o Motor
engine = FolderEngine()
# Inicializa o Gestor de Versões
version_manager = VersionManager("Eddy8080", "Structure-Builder-Pro")


# Função para localizar recursos (necessário para PyInstaller)
def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, funciona para dev e para PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Função para encerrar o processo sem Traceback
def fechar_aplicacao(sig, frame):
    print("\nAplicação encerrada pelo usuário.")
    os._exit(0)

# Registra o tratador de sinal para Ctrl+C (SIGINT)
signal.signal(signal.SIGINT, fechar_aplicacao)

# Configuração do Tkinter para diálogos nativos
def get_root():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    # Busca o ícone de forma compatível com .exe
    icon_path = resource_path("logo.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except:
            pass
            
    return root

@eel.expose
def selecionar_pasta(titulo="Selecionar Pasta"):
    """Abre o seletor de pastas e garante que fique no topo."""
    root = get_root()
    path = filedialog.askdirectory(title=titulo, parent=root)
    root.destroy()
    return path if path else None

@eel.expose
def selecionar_arquivo_salvar(titulo="Salvar Como...", extensao=".json"):
    """Abre o seletor de salvar arquivo."""
    root = get_root()
    path = filedialog.asksaveasfilename(
        title=titulo, 
        defaultextension=extensao,
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        parent=root
    )
    root.destroy()
    return path if path else None

@eel.expose
def abrir_manual():
    """Abre o manual.html de forma compatível com .exe."""
    manual_path = resource_path("manual.html")
    if os.path.exists(manual_path):
        try:
            webbrowser.open(f"file:///{os.path.abspath(manual_path)}")
            return True
        except Exception as e:
            return str(e)
    return f"Arquivo manual.html não encontrado."

@eel.expose
def salvar_modelo_arquivo(path, data):
    """Salva a estrutura atual ou a biblioteca em um arquivo JSON externo."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        return str(e)

@eel.expose
def restaurar_modelos_arquivo():
    """Lê um arquivo JSON e restaura a lista de modelos rápidos."""
    try:
        root = get_root()
        path = filedialog.askopenfilename(
            title="Selecionar Arquivo de Backup de Modelos",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=root
        )
        root.destroy()
        
        if not path: return None
        
        with open(path, 'r', encoding='utf-8') as f:
            novos_modelos = json.load(f)
            
        # Valida se o formato está correto (deve ser uma lista de modelos)
        if isinstance(novos_modelos, list):
            engine.save_quick_templates(novos_modelos)
            return True
        else:
            return "Formato de arquivo inválido para restauração."
    except Exception as e:
        return str(e)

@eel.expose
def obter_modelos_rapidos():
    return engine.load_quick_templates()

@eel.expose
def adicionar_modelo_rapido():
    """Abre seletor de pastas, escaneia estrutura e salva como modelo rápido."""
    try:
        modelos = engine.load_quick_templates()
        if len(modelos) >= 10:
            return {"error": "Limite de 10 modelos atingido. Remova um para adicionar novo."}
            
        root = get_root()
        path = filedialog.askdirectory(title="Selecionar Pasta Real para Salvar como Modelo", parent=root)
        root.destroy()
        
        if not path:
            return None
            
        novo_modelo = engine.scan_physical_structure(path)
        modelos.append(novo_modelo)
        engine.save_quick_templates(modelos)
        
        return {"status": "success", "modelo": novo_modelo}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def remover_modelo_rapido(index):
    """Remove um modelo rápido pelo índice."""
    try:
        modelos = engine.load_quick_templates()
        if 0 <= index < len(modelos):
            modelos.pop(index)
            engine.save_quick_templates(modelos)
            return True
        return False
    except Exception as e:
        return str(e)

@eel.expose
def renomear_modelo_rapido(index, novo_nome):
    """Altera o nome de um modelo rápido e sincroniza com sua estrutura interna."""
    try:
        modelos = engine.load_quick_templates()
        if 0 <= index < len(modelos):
            modelos[index]["main_folder"] = novo_nome
            # Sincroniza o nome no nó raiz da árvore também
            if "tree_structure" in modelos[index]:
                modelos[index]["tree_structure"]["name"] = novo_nome
            engine.save_quick_templates(modelos)
            return True
        return False
    except Exception as e:
        return str(e)

@eel.expose
def atualizar_dados_modelo(index, main_name, tree_data):
    """Atualiza a estrutura de pastas de um modelo no JSON interno."""
    try:
        modelos = engine.load_quick_templates()
        if 0 <= index < len(modelos):
            modelos[index]["main_folder"] = main_name
            modelos[index]["tree_structure"] = tree_data
            engine.save_quick_templates(modelos)
            return True
        return False
    except Exception as e:
        return str(e)

@eel.expose
def sincronizar_no_windows(base_dir, main_folder, tree_data, original_state=None, is_existing=False):
    try:
        return engine.sincronizar_master(base_dir, main_folder, tree_data, original_state, is_existing)
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def aplicar_espelhamento(base_path, tree_data):
    try:
        return engine.sync_mirroring(base_path, tree_data)
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def salvar_copia_estrutura(source, target):
    try:
        res = engine.perform_copy(source, target)
        return True if res == True else {"error": res}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def deletar_estrutura_fisica(path):
    try:
        res = engine.perform_delete_physical(path)
        return True if res == True else {"error": res}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def salvar_estado_espelhamento(data):
    return engine.save_session_state(data)

@eel.expose
def carregar_estado_espelhamento():
    return engine.load_session_state()

@eel.expose
def encerrar_programa():
    """Fecha a aplicação de forma limpa após confirmar com o frontend."""
    import threading
    import time

    def matar_processo():
        time.sleep(0.3) # Delay para o JS receber a resposta
        print("Processo encerrado com sucesso.")
        os._exit(0)

    threading.Thread(target=matar_processo).start()
    return True

@eel.expose
def carregar_estrutura_existente(caminho, incluir_arquivos=False):
    try:
        return engine.load_existing_structure(caminho, incluir_arquivos)
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def criar_nova_estrutura(base_dir, main_folder, tree_data):
    try:
        path = engine.perform_creation(base_dir, main_folder, tree_data)
        return {"status": "success", "path": path}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def atualizar_estrutura(main_name, original_state, current_structure):
    try:
        return engine.perform_update(main_name, original_state, current_structure)
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def confirmar_remocoes(lista_pastas):
    try:
        resultado = engine.finalize_removals(lista_pastas)
        return {"status": "success"} if resultado is True else {"error": resultado}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def verificar_atualizacao_disponivel():
    """Consulta o GitHub e retorna o status para o Frontend."""
    try:
        return version_manager.check_for_updates()
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def obter_informacoes_locais():
    """Retorna a versão instalada no momento."""
    return version_manager.get_local_info()

@eel.expose
def executar_download_e_atualizar(url_download):
    """
    Realiza o download do instalador e inicia o processo de substituição.
    Pilar Técnico: Fluxo do Instalador (Hot-Swap).
    """
    import tempfile
    
    try:
        temp_dir = tempfile.gettempdir()
        dest_path = os.path.join(temp_dir, "StructureBuilderPro_Update.exe")
        
        # Realiza o download físico
        sucesso = version_manager.download_installer(url_download, dest_path)
        
        if sucesso:
            # Engenharia Sênior: Disparo do novo instalador e fechamento do app atual
            # O instalador do Inno Setup cuidará da substituição dos arquivos
            subprocess.Popen([dest_path, '/SILENT', '/SP-'], shell=True)
            
            # Delay mínimo para garantir que o processo do instalador iniciou
            import time
            time.sleep(0.5)
            os._exit(0)
        else:
            return {"error": "Falha crítica no download do instalador."}
    except Exception as e:
        return {"error": str(e)}

def iniciar_app():
    eel.init('web')
    
    # Obtém a resolução real da tela para garantir abertura em tela cheia
    try:
        root = tk.Tk()
        root.withdraw()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        # Define o ícone também na janela oculta que mede a tela (opcional)
        icon_path = resource_path("logo.ico")
        if os.path.exists(icon_path):
            try: root.iconbitmap(icon_path)
            except: pass
        root.destroy()
    except:
        sw, sh = 1200, 800

    # Usar port=0 permite que o sistema escolha automaticamente uma porta livre
    try:
        # Abrimos com as dimensões totais da tela e o comando de maximização
        eel.start('index.html', mode='chrome', port=0, size=(sw, sh), cmdline_args=['--start-maximized'])
    except (SystemExit, MemoryError, KeyboardInterrupt):
        pass
    except EnvironmentError:
        try:
            # Caso o Chrome não esteja disponível, abre no navegador padrão
            eel.start('index.html', mode='default', port=0, size=(sw, sh))
        except (SystemExit, MemoryError, KeyboardInterrupt):
            pass

if __name__ == "__main__":
    try:
        iniciar_app()
    except KeyboardInterrupt:
        fechar_aplicacao(None, None)
