import os
import sys
import tkinter as tk
from tkinter import messagebox
import time
import subprocess

# Engenharia Sênior: Garantindo que o messagebox seja carregado corretamente
import tkinter.messagebox 

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def finalizar_processos_antigos():
    """
    Garante que nenhuma instância do StructureBuilderPro esteja rodando
    para evitar erros de 'Arquivo em Uso' durante a instalação.
    """
    if os.name == 'nt':
        try:
            # Tenta fechar de forma limpa primeiro, depois força se necessário
            subprocess.run(['taskkill', '/F', '/IM', 'StructureBuilderPro.exe', '/T'], 
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            # Também fecha o console de Python se estiver rodando em modo dev
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe', '/T'], 
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

def executar_instalacao_direta(installer_path):
    """
    Modo Sênior: Executa a instalação sem perguntas redundantes,
    mostrando apenas um feedback visual de progresso.
    """
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

        # Centraliza na tela
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"+{(sw//2)-200}+{(sh//2)-60}")

        tk.Label(root, text="Limpando ambiente e iniciando instalador...", 
                 font=("Inter", 10), fg="#f1f5f9", bg="#1e293b", pady=20).pack()
        
        # Barra de progresso fake apenas para feedback visual
        canvas = tk.Canvas(root, width=300, height=10, bg="#0f172a", highlightthickness=0)
        canvas.pack(pady=5)
        bar = canvas.create_rectangle(0, 0, 0, 10, fill="#10b981", outline="")

        def step(n):
            if n <= 300:
                canvas.coords(bar, 0, 0, n, 10)
                if n == 150: # No meio do caminho, limpa os processos
                    finalizar_processos_antigos()
                root.after(10, lambda: step(n + 5))
            else:
                try:
                    os.startfile(installer_path)
                    root.destroy()
                    sys.exit(0)
                except Exception as e:
                    tkinter.messagebox.showerror("Erro Crítico", f"Falha ao abrir instalador:\n{str(e)}")
                    root.destroy()
                    sys.exit(1)

        root.after(500, lambda: step(0))
        root.mainloop()

    except Exception as e:
        finalizar_processos_antigos()
        os.startfile(installer_path)
        sys.exit(0)

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    installer_path = os.path.abspath(sys.argv[1])
    
    # Aguarda o bridge encerrar graciosamente por 1 segundo
    time.sleep(1.0)

    if not os.path.exists(installer_path):
        sys.exit(1)

    # Agora o Sidecar assume que se foi chamado pelo bridge, 
    # a confirmação já foi feita na Web.
    executar_instalacao_direta(installer_path)

if __name__ == "__main__":
    main()
