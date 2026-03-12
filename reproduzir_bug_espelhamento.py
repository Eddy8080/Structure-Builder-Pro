import os
import shutil
from folder_engine import FolderEngine

def reproduzir():
    engine = FolderEngine()
    test_root = os.path.abspath("TESTE_REPRODUCAO_ESPELHAMENTO")
    
    if os.path.exists(test_root):
        shutil.rmtree(test_root)
    os.makedirs(test_root)

    # Passo 1: Criar cenário inicial
    # Pasta raiz: Projeto A
    #   - Arquivo 1.txt
    #   - Arquivo 2.txt
    #   - Subpasta/
    #     - SubArquivo.txt
    
    base_path = os.path.join(test_root, "ProjetoA")
    os.makedirs(base_path)
    with open(os.path.join(base_path, "Arquivo1.txt"), "w") as f: f.write("conteudo 1")
    with open(os.path.join(base_path, "Arquivo2.txt"), "w") as f: f.write("conteudo 2")
    os.makedirs(os.path.join(base_path, "Subpasta"))
    with open(os.path.join(base_path, "Subpasta", "SubArquivo.txt"), "w") as f: f.write("sub")

    print(f"Cenário criado em: {base_path}")

    # Passo 2: Simular o carregamento pela UI
    # A UI chama carregar_estrutura_existente(path, include_files=True)
    dados = engine.load_existing_structure(base_path, include_files=True)
    tree_data = dados['tree_structure']
    
    # Vamos conferir se carregou tudo
    print("Estrutura carregada:")
    def print_tree(node, indent=0):
        print("  " * indent + f"- {node['name']} ({node['type']})")
        for child in node.get('children', []):
            print_tree(child, indent + 1)
    
    print_tree(tree_data)

    # Passo 3: Simular renomeação de 'Subpasta' para 'SubpastaRenomeada'
    for child in tree_data['children']:
        if child['name'] == "Subpasta":
            child['name'] = "SubpastaRenomeada"
            print("\nRenomeando 'Subpasta' para 'SubpastaRenomeada' na árvore virtual...")
            break

    # Passo 4: Aplicar espelhamento
    print("\nAplicando espelhamento (sync_mirroring)...")
    try:
        resultado = engine.sync_mirroring(base_path, tree_data)
        if resultado.get("error"):
            print(f"Erro no motor: {resultado['error']}")
    except Exception as e:
        print(f"Exceção: {e}")

    # Passo 5: Validar o disco
    print("\nValidando estado do disco após sincronização:")
    arquivos_base = os.listdir(base_path)
    print(f"Arquivos na raiz: {arquivos_base}")
    
    falha = False
    if "ArquivoRenomeado.txt" not in arquivos_base:
        print("[ERRO] Arquivo renomeado não encontrado!")
        falha = True
    if "Arquivo2.txt" not in arquivos_base:
        print("[ERRO FATAL] Arquivo2.txt foi DELETADO indevidamente!")
        falha = True
    if "Subpasta" not in arquivos_base:
        print("[ERRO FATAL] Subpasta foi DELETADA indevidamente!")
        falha = True
    else:
        sub_files = os.listdir(os.path.join(base_path, "Subpasta"))
        if "SubArquivo.txt" not in sub_files:
            print("[ERRO FATAL] Conteúdo da Subpasta foi DELETADO indevidamente!")
            falha = True

    if not falha:
        print("\n[OK] O sistema se comportou corretamente neste teste isolado.")
    else:
        print("\n[BUG REPRODUZIDO] Perda de dados detectada.")

if __name__ == "__main__":
    reproduzir()
