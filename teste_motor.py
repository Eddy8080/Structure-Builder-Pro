import os
import shutil
from folder_engine import FolderEngine

def executar_testes():
    engine = FolderEngine()
    test_root = os.path.join(os.getcwd(), "TESTE_AUTOMATICO_MOTOR")
    
    # Limpa ambiente de teste anterior se existir
    if os.path.exists(test_root):
        shutil.rmtree(test_root)
    os.makedirs(test_root)

    print("=== INICIANDO TESTES DO MOTOR (FOLDER_ENGINE) ===")

    # 1. Teste de Sanitização
    print("\n1. Testando Sanitização...")
    nome_sujo = 'Pasta*Com?Caracteres:Invalidos'
    nome_limpo = engine._sanitize_path(nome_sujo)
    esperado = 'PastaComCaracteresInvalidos'
    if nome_limpo == esperado:
        print(f"   [OK] Sanitização simples: '{nome_sujo}' -> '{nome_limpo}'")
    else:
        print(f"   [ERRO] Sanitização falhou! Esperado: {esperado}, Obtido: {nome_limpo}")

    # 2. Teste de Criação Física
    print("\n2. Testando Criação de Estrutura...")
    main_folder = "Cliente_Teste_Alfa"
    subfolders = [
        {"name": "Documentos"},
        {"name": "Fotos/2024"},
        {"name": "Financeiro/Notas_Fiscais"}
    ]
    
    try:
        path_criado = engine.perform_creation(test_root, main_folder, subfolders)
        if os.path.exists(path_criado) and os.path.exists(os.path.join(path_criado, "Fotos", "2024")):
            print(f"   [OK] Estrutura física criada em: {path_criado}")
        else:
            print("   [ERRO] A estrutura física não foi encontrada no disco.")
    except Exception as e:
        print(f"   [ERRO] Exceção na criação: {e}")

    # 3. Teste de Leitura (Scan)
    print("\n3. Testando Leitura de Estrutura Existente...")
    try:
        dados_lidos = engine.load_existing_structure(path_criado)
        if dados_lidos['main_folder'] == main_folder and len(dados_lidos['subfolders']) >= 3:
            print(f"   [OK] Motor leu corretamente a pasta '{main_folder}' com {len(dados_lidos['subfolders'])} itens.")
        else:
            print(f"   [ERRO] Dados lidos incorretos: {dados_lidos}")
    except Exception as e:
        print(f"   [ERRO] Exceção na leitura: {e}")

    # 4. Teste de Lógica de Atualização (O mais sensível)
    print("\n4. Testando Lógica de Atualização (Rename e Delete)...")
    # Simulação: Renomear pasta principal e remover a pasta 'Documentos'
    novo_nome_main = "Cliente_Teste_Beta"
    estado_original = dados_lidos
    # Nova estrutura sem a pasta 'Documentos' e com uma nova 'Contratos'
    nova_estrutura = [
        {"name": "Fotos/2024", "original_path": os.path.join(path_criado, "Fotos", "2024")},
        {"name": "Financeiro/Notas_Fiscais", "original_path": os.path.join(path_criado, "Financeiro", "Notas_Fiscais")},
        {"name": "Contratos", "original_path": ""} # Pasta nova
    ]

    try:
        resultado_update = engine.perform_update(novo_nome_main, estado_original, nova_estrutura)
        
        # Verifica se o motor identificou a pasta removida (Documentos)
        removidos = resultado_update['removed_folders']
        pasta_doc_original = os.path.join(path_criado, "Documentos")
        
        if any(os.path.normpath(pasta_doc_original) in os.path.normpath(r) for r in removidos):
            print("   [OK] Motor identificou corretamente a pasta para remoção: 'Documentos'")
            # Executa a remoção física para completar o teste
            engine.finalize_removals(removidos)
            if not os.path.exists(pasta_doc_original):
                print("   [OK] Remoção física executada com sucesso.")
        else:
            print(f"   [ERRO] Motor NÃO identificou a remoção. Removidos: {removidos}")
            
        if "Beta" in resultado_update['effective_path']:
             print(f"   [OK] Novo caminho efetivo correto: {resultado_update['effective_path']}")

    except Exception as e:
        print(f"   [ERRO] Exceção no update: {e}")

    print("\n=== TESTES CONCLUÍDOS ===")
    print(f"\nOs arquivos de teste foram mantidos em:\n{test_root}\nVocê pode conferir as pastas manualmente.")

if __name__ == "__main__":
    executar_testes()
