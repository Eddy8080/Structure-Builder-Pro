import time
import threading
import os
import sys
import ctypes

# Identidade visual única da Anagma
# DEVE ser idêntica à do bridge.py e à AppId do installer_config.iss
APP_ID = 'Anagma.StructureBuilderPro.v5'
WINDOW_TITLE = 'Structure Builder Pro'
CHROMIUM_CLASS = 'Chrome_WidgetWin_1' # Classe comum ao Google Chrome e Microsoft Edge

def fixar_identidade_visual():
    """
    Localiza a janela Chromium e força a identidade da Anagma.
    Implementa um ciclo de reforço para evitar que o browser recupere o controle do ícone.
    """
    # 1. Identidade no nível do processo pai (Python/EXE)
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except:
        pass

    if not getattr(sys, 'frozen', False):
        return False

    exe_path = sys.executable

    # 2. Monitoramento Agressivo (Ciclo de Reforço)
    # O Chromium tenta definir seu próprio AppID milissegundos após a criação da janela.
    # Por isso, aplicaremos o carimbo logo que a janela surgir e reforçaremos depois.
    for _ in range(60):
        # Busca pela classe nativa do motor gráfico (Chromium) vinculada ao título do projeto
        hwnd = ctypes.windll.user32.FindWindowW(CHROMIUM_CLASS, WINDOW_TITLE)
        if hwnd:
            # Primeira aplicação (imediata ao detectar a janela)
            _injetar_propriedades_relaunch(hwnd, exe_path)
            
            # Pequena pausa estratégica para aguardar o carregamento completo do motor gráfico
            time.sleep(2.5)
            
            # Segunda aplicação (reforço final para consolidar a fixação)
            _injetar_propriedades_relaunch(hwnd, exe_path)
            
            print(f"[DEBUG] Identidade Anagma consolidada com sucesso.")
            return True
        time.sleep(0.5)
    return False

def _injetar_propriedades_relaunch(hwnd, exe_path):
    """
    Injeta propriedades de Shell diretamente no Handle da Janela (HWND).
    Utiliza as bibliotecas nativas de sistema para vincular o ícone ao executável.
    """
    try:
        # Importações tardias para garantir que o ambiente Windows esteja pronto
        import pythoncom
        from win32com.propsys import propsys, pscon
        from win32com.shell import shellcon
        
        # Inicializa o subsistema de comunicação com o Windows (COM)
        pythoncom.CoInitialize()
        
        # Acessa a Loja de Propriedades da Janela ativa
        prop_store = propsys.SHGetPropertyStoreForWindow(hwnd, shellcon.IID_IPropertyStore)
        
        # 1. Define o ID único para Agrupamento na barra de tarefas
        prop_store.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType(APP_ID))
        
        # 2. Define o Comando de Relançamento (O segredo para abrir o .exe ao clicar no fixado)
        prop_store.SetValue(pscon.PKEY_AppUserModel_RelaunchCommand, propsys.PROPVARIANTType(exe_path))
        
        # 3. Define o Nome de Exibição do Aplicativo
        prop_store.SetValue(pscon.PKEY_AppUserModel_RelaunchDisplayNameResource, propsys.PROPVARIANTType(WINDOW_TITLE))
        
        # 4. Define o ícone do atalho como sendo o ícone embutido no executável
        prop_store.SetValue(pscon.PKEY_AppUserModel_RelaunchIconResource, propsys.PROPVARIANTType(f"{exe_path},0"))
        
        # Consolida as propriedades no Windows Shell
        prop_store.Commit()
        
    except Exception as e:
        # Falha silenciosa para não interromper a interface do usuário
        pass
    finally:
        try:
            pythoncom.CoUninitialize()
        except:
            pass

def iniciar_monitoramento_janela():
    """Dispara o vigilante de identidade visual em uma thread assíncrona."""
    thread = threading.Thread(target=fixar_identidade_visual, daemon=True)
    thread.start()
