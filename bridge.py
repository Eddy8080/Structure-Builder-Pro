import ctypes
import os
import sys

# Identificador único para a barra de tarefas do Windows (AppUserModelID)
# Sincronizado com o instalador para garantir a identidade visual única do projeto.
myappid = 'Anagma.StructureBuilderPro.v5' 
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# Engenharia Sênior: Isolamento de Diretório Base
# Garante que o programa sempre opere em seu diretório de instalação ou de script,
# impedindo contaminação entre a versão instalada e a pasta do projeto.
if getattr(sys, 'frozen', False):
    # Ambiente Executável: Força o contexto para a pasta onde o .exe está
    base_dir_context = os.path.dirname(sys.executable)
else:
    # Ambiente Desenvolvimento: Força o contexto para a pasta do script bridge.py
    base_dir_context = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir_context)
print(f"Contexto de execução isolado em: {os.getcwd()}")

import eel
import tkinter as tk
from tkinter import filedialog
import subprocess
import json
import signal 
import webbrowser
from folder_engine import FolderEngine
from version_control import VersionManager
from window_manager import iniciar_monitoramento_janela

# Inicializa o Motor
engine = FolderEngine()
# Inicializa o Gestor de Versões
version_manager = VersionManager("Eddy8080", "Structure-Builder-Pro")

# Engenharia Sênior: Lógica de Suporte ao Modo Sidecar (Executável Único)
def finalizar_processos_antigos_sidecar():
    if os.name == 'nt':
        try:
            # Mata o executável principal para liberar o arquivo para o instalador
            subprocess.run(['taskkill', '/F', '/IM', 'StructureBuilderPro.exe', '/T'], 
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
    import time
    time.sleep(0.5)

def executar_logica_sidecar(installer_path):
    """Feedback visual e execução do instalador (Integrado no Executável Único)."""
    import tkinter as tk
    from tkinter import messagebox
    import time
    
    try:
        root = tk.Tk()
        root.title("Preparando Atualização")
        root.geometry("400x120")
        root.resizable(False, False)
        root.configure(bg="#1e293b")
        root.attributes("-topmost", True)

        icon_path = resource_path("logo.ico")
        if os.path.exists(icon_path):
            try: root.iconbitmap(icon_path)
            except: pass

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"+{(sw//2)-200}+{(sh//2)-60}")

        tk.Label(root, text="Limpando ambiente e iniciando instalador...", 
                 font=("Inter", 10), fg="#f1f5f9", bg="#1e293b", pady=20).pack()
        
        canvas = tk.Canvas(root, width=300, height=10, bg="#0f172a", highlightthickness=0)
        canvas.pack(pady=5)
        bar = canvas.create_rectangle(0, 0, 0, 10, fill="#10b981", outline="")

        def step(n):
            if n <= 300:
                canvas.coords(bar, 0, 0, n, 10)
                if n == 150: finalizar_processos_antigos_sidecar()
                root.after(10, lambda: step(n + 5))
            else:
                try:
                    os.startfile(installer_path)
                    root.destroy()
                    os._exit(0)
                except Exception as e:
                    tk.messagebox.showerror("Erro Crítico", f"Falha ao abrir instalador:\n{str(e)}")
                    root.destroy()
                    os._exit(1)

        root.after(500, lambda: step(0))
        root.mainloop()
    except Exception:
        finalizar_processos_antigos_sidecar()
        os.startfile(installer_path)
        os._exit(0)

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
    Fluxo Sênior com Sidecar: 
    1. Faz o download para pasta Temp.
    2. Dispara o vigilante (Sidecar) para gerenciar o fechamento e instalação.
    3. Suicida o processo principal.
    """
    import tempfile
    try:
        # Caminho absoluto e normalizado no Temp do Windows
        dest_path = os.path.normpath(os.path.join(tempfile.gettempdir(), "StructureBuilderPro_Update.exe"))
        
        def progresso_callback(percent):
            eel.atualizar_progresso_download(round(percent, 1))
        
        print(f"[UPDATE] Iniciando download: {dest_path}")
        sucesso = version_manager.download_installer(url_download, dest_path, progress_callback=progresso_callback)
        
        if sucesso:
            print(f"[UPDATE] Download concluído com sucesso em: {dest_path}")
            return {"success": True, "installer_path": dest_path}
        else:
            return {"error": "Falha no download. Verifique sua conexão."}
    except Exception as e:
        print(f"[UPDATE] Erro Crítico: {e}")
        return {"error": str(e)}

@eel.expose
def finalizar_e_instalar(installer_path):
    """
    Acionado pelo Frontend após confirmação do usuário.
    Inicia o PRÓPRIO executável em modo sidecar a partir de um local neutro.
    """
    try:
        import shutil
        import tempfile
        print("[UPDATE] Preparando execução neutra do modo sidecar...")
        
        if getattr(sys, 'frozen', False):
            # O próprio executável principal atua como sidecar
            original_exe = sys.executable
            
            temp_dir = tempfile.gettempdir()
            neutral_updater = os.path.join(temp_dir, "SBPro_Updater_Runner.exe")
            
            try:
                # Cria uma cópia de escape do próprio EXE
                shutil.copy2(original_exe, neutral_updater)
                
                # Executa a cópia com a flag de modo sidecar
                subprocess.Popen([neutral_updater, "--sidecar-mode", installer_path], shell=False, 
                                 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            except Exception as e:
                print(f"[UPDATE] Falha na cópia neutra, tentando fallback direto: {e}")
                subprocess.Popen([original_exe, "--sidecar-mode", installer_path], shell=False, 
                                 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            # Modo Desenvolvimento: roda o script principal com a flag
            main_script = os.path.abspath(__file__)
            subprocess.Popen([sys.executable, main_script, "--sidecar-mode", installer_path], shell=False,
                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        
        # Encerramento diferido para permitir que o JS execute window.close()
        import threading
        def delayed_exit():
            import time
            time.sleep(1.0)
            os._exit(0)
            
        threading.Thread(target=delayed_exit, daemon=True).start()
        return True
    except Exception as e:
        print(f"[UPDATE] Erro Crítico ao disparar modo sidecar: {e}")
        return {"error": str(e)}

@eel.expose
def mr_selecionar_pasta_modelo():
    """Abre seletor de pasta e retorna o caminho e nome da pasta modelo."""
    root = get_root()
    path = filedialog.askdirectory(title="Selecionar Pasta Modelo", parent=root)
    root.destroy()
    if not path:
        return None
    nome = os.path.basename(path)
    return {"path": path, "name": nome}

@eel.expose
def mr_selecionar_raiz_busca():
    """Abre seletor para definir a unidade/pasta raiz onde a busca será feita."""
    root = get_root()
    path = filedialog.askdirectory(title="Selecionar Unidade ou Pasta Raiz para Busca", parent=root)
    root.destroy()
    return path if path else None

@eel.expose
def mr_buscar_pastas(nome_padrao, raiz_busca):
    """Busca recursiva profunda por pastas com nome exato igual ao padrão."""
    resultados = []
    try:
        raiz_busca = os.path.normpath(raiz_busca)
        for dirpath, dirnames, _ in os.walk(raiz_busca):
            for d in dirnames:
                if d == nome_padrao:
                    resultados.append(os.path.join(dirpath, d).replace("\\", "/"))
        return {"status": "success", "resultados": resultados, "total": len(resultados)}
    except PermissionError as e:
        return {"status": "partial", "resultados": resultados, "total": len(resultados), "aviso": str(e)}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def mr_aplicar_renomeacao(resultados, novo_nome):
    """
    Para cada pasta encontrada:
    1. Cria nova pasta com novo_nome no mesmo diretório pai.
    2. Copia o conteúdo da pasta original para a nova.
    3. Move a pasta original para subpasta 'Antigos' no mesmo diretório pai.
    Retorna relatório com sucesso e erros.
    """
    import shutil
    import time
    sucesso = []
    erros = []

    for caminho_original in resultados:
        try:
            caminho_original = os.path.normpath(caminho_original)
            pai = os.path.dirname(caminho_original)
            nome_original = os.path.basename(caminho_original)
            nova_pasta = os.path.join(pai, novo_nome)
            pasta_antigos = os.path.join(pai, "Antigos")

            # Garante que a pasta "Antigos" existe
            os.makedirs(pasta_antigos, exist_ok=True)

            # Cria nova pasta com o novo nome
            os.makedirs(nova_pasta, exist_ok=True)

            # Copia conteúdo da pasta original para a nova
            for item in os.listdir(caminho_original):
                src = os.path.join(caminho_original, item)
                dst = os.path.join(nova_pasta, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

            # Move pasta original para "Antigos" (evita colisão de nomes)
            destino_antigos = os.path.join(pasta_antigos, nome_original)
            if os.path.exists(destino_antigos):
                destino_antigos = os.path.join(pasta_antigos, f"{nome_original}_{int(time.time())}")
            shutil.move(caminho_original, destino_antigos)

            sucesso.append(caminho_original.replace("\\", "/"))
        except Exception as e:
            erros.append({"path": caminho_original.replace("\\", "/"), "error": str(e)})

    return {"sucesso": sucesso, "erros": erros}


def iniciar_app():
    # Engenharia Sênior: Força a inicialização a partir do recurso embutido (_MEIPASS)
    web_resource_path = resource_path('web')
    eel.init(web_resource_path)

    try:
        root = tk.Tk()
        root.withdraw()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        icon_path = resource_path("logo.ico")
        if os.path.exists(icon_path):
            try: root.iconbitmap(icon_path)
            except: pass
        root.destroy()
    except:
        sw, sh = 1200, 800

    # Engenharia Sênior: Isolamento de Perfil para Fixação Precisa de Ícone
    user_data_dir = os.path.join(engine.app_data_dir, "SBPro_Profile")
    if not os.path.exists(user_data_dir):
        try: os.makedirs(user_data_dir, exist_ok=True)
        except: pass

    # Engenharia Sênior: Dispara o monitor de identidade visual
    iniciar_monitoramento_janela()

    try:
        # Abrimos em modo App com isolamento total de perfil e identidade vinculada
        eel.start('index.html', 
                  mode='chrome', 
                  port=0, 
                  size=(sw, sh), 
                  cmdline_args=[
                      '--start-maximized', 
                      f'--app-id={myappid}',
                      f'--user-data-dir={user_data_dir}',
                      '--no-first-run',
                      '--no-default-browser-check'
                  ])
    except (SystemExit, MemoryError, KeyboardInterrupt):
        pass
    except EnvironmentError:
        try:
            eel.start('index.html', mode='default', port=0, size=(sw, sh))
        except (SystemExit, MemoryError, KeyboardInterrupt):
            pass

if __name__ == "__main__":
    # Verifica se o programa deve iniciar em modo de atualização (Sidecar)
    if len(sys.argv) >= 3 and sys.argv[1] == "--sidecar-mode":
        installer_path = sys.argv[2]
        executar_logica_sidecar(installer_path)
    else:
        try:
            iniciar_app()
        except KeyboardInterrupt:
            fechar_aplicacao(None, None)
