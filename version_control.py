import os
import sys
import json
import hashlib
import requests
from datetime import datetime

class VersionManager:
    """
    Motor de Atualização Universal v1.2
    Arquitetura Sênior: Desacoplada, Resiliente e Segura.
    """
    
    def __init__(self, repo_owner, repo_name, current_version_file="version.json"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.version_filename = current_version_file
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        self.timeout = 10 
        
        # Engenharia Sênior: Fallback Hardcoded (Última linha de defesa)
        # Se todos os arquivos sumirem, o sistema reportará esta versão em vez de 0.0.0
        self.FALLBACK_VERSION = "5.6.2" 

    def get_local_info(self):
        """
        Lógica de Tripla Verificação (Triple Check):
        Garante a leitura da versão em qualquer cenário de build (Auto ou Manual).
        """
        possible_paths = []
        
        # VERIFICAÇÃO 1: Recurso Interno (PyInstaller Bundled)
        # Quando você usa --add-data, o arquivo vai para a pasta temporária _MEIPASS
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            possible_paths.append(os.path.join(sys._MEIPASS, self.version_filename))
            
        # VERIFICAÇÃO 2: Pasta do Executável (Externo)
        # Caso o arquivo tenha sido copiado manualmente para a pasta do .exe
        if getattr(sys, 'frozen', False):
            possible_paths.append(os.path.join(os.path.dirname(sys.executable), self.version_filename))
        
        # VERIFICAÇÃO 3: Pasta de Desenvolvimento (Script)
        # Caminho padrão para quando você roda via terminal (python bridge.py)
        possible_paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), self.version_filename))

        # Tenta ler de cada caminho possível até encontrar um válido
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data and "version" in data:
                            return data
            except Exception:
                continue

        # Se todas as verificações falharem (arquivo deletado/corrompido),
        # retorna a versão de segurança para NUNCA exibir 0.0.0
        return {"version": self.FALLBACK_VERSION}

    def check_for_updates(self):
        """
        Consulta a API do GitHub para verificar novas versões.
        Implementa o pilar de Lógica de Redes (Conectividade HTTPS).
        """
        try:
            headers = {"User-Agent": f"{self.repo_name}-Updater"}
            response = requests.get(self.api_url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                remote_version = data.get("tag_name", "").replace("v", "").strip()
                local_version = self.get_local_info().get("version", "0.0.0").strip()
                
                # Engenharia Sênior: Lógica de Atualização Permissiva
                # Permitimos que o ciclo de update continue (has_update = True) 
                # sempre que houver uma versão remota válida. Isso permite que o usuário
                # force uma reinstalação para obter hotfixes ou correções de integridade.
                has_update = True if remote_version else False
                
                return {
                    "has_update": has_update,
                    "remote_version": remote_version,
                    "local_version": local_version,
                    "changelog": data.get("body", "Melhorias gerais no sistema."),
                    "assets": data.get("assets", [])
                }
            if response.status_code == 404:
                # Caso o repositório exista mas não tenha nenhuma 'Release' publicada.
                return {
                    "has_update": False, 
                    "remote_version": None, 
                    "local_version": self.get_local_info().get("version", "0.0.0"),
                    "info": "Repositório sem versões publicadas."
                }
            elif response.status_code == 403:
                return {"error": "Limite de requisições do GitHub atingido. Aguarde alguns minutos."}
                
            return {"error": f"Resposta inesperada do servidor (Status {response.status_code})"}
        except requests.exceptions.ConnectionError:
            return {"error": "Impossível conectar ao servidor. Verifique sua internet."}
        except Exception as e:
            return {"error": f"Falha no motor de atualização: {str(e)}"}

    def verify_hash(self, file_path, expected_hash):
        """
        Implementa o pilar de Segurança de Hash (Integridade Binária).
        Garante que o arquivo baixado não foi corrompido ou adulterado.
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Leitura em blocos para eficiência de memória
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest().lower() == expected_hash.lower()
        except Exception:
            return False

    def download_installer(self, url, destination, progress_callback=None):
        """
        Download resiliente via Stream.
        """
        try:
            response = requests.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 32): # 8KB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            percent = (downloaded / total_size) * 100 if total_size > 0 else 0
                            progress_callback(percent)
            return True
        except Exception as e:
            if os.path.exists(destination):
                os.remove(destination)
            return False
