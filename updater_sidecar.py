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
        except:
            pass

def iniciar_confirmacao_visual(installer_path):
    try:
        root = tk.Tk()
        root.title("Structure Builder Pro - Atualização")
        root.geometry("450x220")
        root.resizable(False, False)
        root.configure(bg="#1e293b")
        root.attributes("-topmost", True)

        icon_path = resource_path("logo.ico")
        if os.path.exists(icon_path):
            try: root.iconbitmap(icon_path)
            except: pass

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw // 2) - (450 // 2)
        y = (sh // 2) - (220 // 2)
        root.geometry(f"+{x}+{y}")

        tk.Label(root, text="Download Concluído!", font=("Inter", 14, "bold"), fg="#10b981", bg="#1e293b", pady=15).pack()
        
        msg = "O instalador da nova versão está pronto.\n\nDeseja fechar o programa e iniciar a instalação agora?"
        tk.Label(root, text=msg, font=("Inter", 10), fg="#f1f5f9", bg="#1e293b", wraplength=400, justify="center").pack(pady=10)

        btn_frame = tk.Frame(root, bg="#1e293b")
        btn_frame.pack(pady=20)

        def on_confirm():
            # Fecha a janela ANTES de disparar
            root.withdraw() 
            try:
                # Engenharia Sênior: Garante que o processo principal morreu antes de chamar o instalador
                finalizar_processos_antigos()
                time.sleep(0.5)
                
                os.startfile(installer_path)
                root.destroy()
                sys.exit(0)
            except Exception as e:
                tkinter.messagebox.showerror("Erro Crítico", f"Falha ao abrir instalador:\n{str(e)}")
                root.destroy()
                sys.exit(1)

        def on_cancel():
            root.destroy()
            sys.exit(0)

        tk.Button(btn_frame, text="Sim, Instalar Agora", font=("Inter", 10, "bold"), 
                  fg="#ffffff", bg="#10b981", padx=20, pady=5, border=0, cursor="hand2", command=on_confirm).pack(side="left", padx=10)

        tk.Button(btn_frame, text="Cancelar", font=("Inter", 10), 
                  fg="#ffffff", bg="#64748b", padx=20, pady=5, border=0, cursor="hand2", command=on_cancel).pack(side="left", padx=10)

        root.mainloop()
    except Exception as e:
        finalizar_processos_antigos()
        os.startfile(installer_path)
        sys.exit(0)

def main():
    # O sidecar recebe o caminho do instalador como argumento
    if len(sys.argv) < 2:
        sys.exit(1)

    installer_path = os.path.abspath(sys.argv[1])
    
    # Aguarda o bridge encerrar graciosamente por 2 segundos
    time.sleep(2.0)

    if not os.path.exists(installer_path):
        sys.exit(1)

    iniciar_confirmacao_visual(installer_path)

if __name__ == "__main__":
    main()
