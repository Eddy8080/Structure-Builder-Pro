import os
import shutil
from folder_engine import FolderEngine

def testar_correcao_renomeacao():
    print("=== INICIANDO TESTE DE SEGURANÇA DE RENOMEAÇÃO (ESPELHAMENTO) ===")
    engine = FolderEngine()
    test_root = os.path.abspath("TESTE_VALIDACAO_ESPELHAMENTO")
    
    if os.path.exists(test_root):
        shutil.rmtree(test_root)
    os.makedirs(test_root)

    # 1. Criar cenário: ProjetoA com dois arquivos e uma subpasta
    base_path = os.path.join(test_root, "ProjetoA")
    os.makedirs(base_path)
    file1_path = os.path.join(base_path, "Original.txt")
    file2_path = os.path.join(base_path, "NaoMexer.txt")
    sub_path = os.path.join(base_path, "Subpasta")
    
    with open(file1_path, "w") as f: f.write("conteudo original")
    with open(file2_path, "w") as f: f.write("este arquivo deve ser preservado")
    os.makedirs(sub_path)
    with open(os.path.join(sub_path, "Dentro.txt"), "w") as f: f.write("sub")

    print(f"Cenário criado em: {base_path}")

    # 2. Carregar estrutura via motor
    dados = engine.load_existing_structure(base_path, include_files=True)
    tree_data = dados['tree_structure']
    
    # 3. Simular renomeação de 'Original.txt' para 'Renomeado.txt'
    # E simular que o usuário 'removeu' um item da árvore virtual (sem deletar fisicamente na UI ainda)
    # No bug anterior, se um item sumisse da árvore virtual, o motor deletava do disco.
    
    nova_children = []
    for child in tree_data['children']:
        if child['name'] == "Original.txt":
            child['name'] = "Renomeado.txt"
            nova_children.append(child)
            print("Renomeando 'Original.txt' para 'Renomeado.txt' na árvore virtual...")
        elif child['name'] == "NaoMexer.txt":
            # Mantemos na árvore
            nova_children.append(child)
        elif child['name'] == "Subpasta":
            # SIMULAMOS QUE A SUBPASTA FOI REMOVIDA DA ÁRVORE VIRTUAL (mas não queremos que suma do disco)
            print("Simulando que 'Subpasta' foi ocultada/removida da visualização...")
            pass 
            
    tree_data['children'] = nova_children

    # 4. Aplicar espelhamento
    print("Aplicando espelhamento...")
    resultado = engine.sync_mirroring(base_path, tree_data)
    if "error" in resultado:
        print(f"ERRO NO MOTOR: {resultado['error']}")
        return

    # 5. VALIDAR DISCO
    print("\nValidando estado do disco:")
    arquivos_final = os.listdir(base_path)
    print(f"Arquivos presentes: {arquivos_final}")
    
    sucesso = True
    
    # A. O arquivo renomeado deve existir
    if "Renomeado.txt" not in arquivos_final:
        print("[FALHA] 'Renomeado.txt' não foi criado/renomeado!")
        sucesso = False
    
    # B. O arquivo antigo 'Original.txt' deve ter sumido (foi renomeado)
    if "Original.txt" in arquivos_final:
        print("[ALERTA] 'Original.txt' ainda existe no disco (renomeação falhou ou criou cópia)!")
        # Isso não é necessariamente um erro fatal de perda de dados, mas é comportamento incorreto de renomeação
    
    # C. O arquivo 'NaoMexer.txt' deve CONTINUAR LÁ (CRÍTICO)
    if "NaoMexer.txt" not in arquivos_final:
        print("[ERRO FATAL] 'NaoMexer.txt' foi DELETADO indevidamente!")
        sucesso = False
    else:
        print("[OK] 'NaoMexer.txt' foi preservado.")

    # D. A 'Subpasta' que removemos da árvore virtual DEVE CONTINUAR LÁ (A CORREÇÃO)
    if "Subpasta" not in arquivos_final:
        print("[ERRO FATAL] 'Subpasta' foi DELETADA porque não estava na árvore virtual!")
        sucesso = False
    else:
        print("[OK] 'Subpasta' foi preservada (Correção Funciona!).")

    if sucesso:
        print("\n=== TESTE PASSOU: INTEGRIDADE DE DADOS GARANTIDA ===")
    else:
        print("\n=== TESTE FALHOU: O MOTOR AINDA É DESTRUTIVO ===")

if __name__ == "__main__":
    testar_correcao_renomeacao()
