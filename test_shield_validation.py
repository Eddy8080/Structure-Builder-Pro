import os
import sys
import shutil
from folder_engine import FolderEngine

def test_shield():
    print("=== INICIANDO VALIDAÇÃO DE BLINDAGEM (PATH SHIELDING) ===\n")
    engine = FolderEngine()
    
    # Identifica a zona protegida (neste caso, a pasta do projeto)
    protected_zone = engine.app_home
    print(f"[TEST] Zona Protegida Detectada: {protected_zone}")
    
    # 1. Teste de Espelhamento (sync_mirroring) para dentro do projeto
    print("\n[TEST 1] Tentando espelhar para dentro do projeto...")
    fake_tree = {
        "name": "Tentativa_Invasao",
        "type": "directory",
        "children": []
    }
    # Tenta espelhar para uma subpasta inexistente dentro do projeto
    target_inside = os.path.join(protected_zone, "subpasta_teste_bloqueio")
    result = engine.sync_mirroring(target_inside, fake_tree)
    
    if "error" in result and "Operação de Espelhamento Bloqueada" in result["error"]:
        print("✅ SUCESSO: Espelhamento para o projeto foi bloqueado corretamente.")
    else:
        print(f"❌ FALHA: O sistema permitiu ou retornou erro inesperado: {result}")

    # 2. Teste de Cópia (perform_copy) para dentro do projeto
    print("\n[TEST 2] Tentando copiar estrutura para dentro do projeto...")
    # Criar uma pasta temporária externa para ser a "origem"
    temp_source = os.path.abspath("TESTE_ORIGEM_TEMP")
    os.makedirs(temp_source, exist_ok=True)
    
    target_copy = os.path.join(protected_zone, "copia_proibida")
    result_copy = engine.perform_copy(temp_source, target_copy)
    
    if "Operação Bloqueada" in str(result_copy):
        print("✅ SUCESSO: Cópia para o projeto foi bloqueada corretamente.")
    else:
        print(f"❌ FALHA: O sistema permitiu a cópia: {result_copy}")
    
    shutil.rmtree(temp_source)

    # 3. Teste de Deleção (perform_delete_physical) de arquivo do projeto
    print("\n[TEST 3] Tentando deletar a própria pasta do projeto pela interface...")
    result_del = engine.perform_delete_physical(protected_zone)
    
    if "Operação Bloqueada" in str(result_del):
        print("✅ SUCESSO: Deleção da pasta do projeto foi bloqueada corretamente.")
    else:
        print(f"❌ FALHA: O sistema permitiu a tentativa de deleção: {result_del}")

    # 4. Teste de Criação de Template (sincronizar_master) dentro do projeto
    print("\n[TEST 4] Tentando criar novo template dentro do projeto...")
    result_master = engine.sincronizar_master(protected_zone, "Template_Invasor", fake_tree)
    
    if "error" in result_master and "Operação Bloqueada" in result_master["error"]:
        print("✅ SUCESSO: Criação de template no projeto foi bloqueada corretamente.")
    else:
        print(f"❌ FALHA: O sistema permitiu a criação: {result_master}")

    print("\n=== VALIDAÇÃO CONCLUÍDA ===")

if __name__ == "__main__":
    test_shield()
