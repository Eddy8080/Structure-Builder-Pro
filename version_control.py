import os
import json
import hashlib
import requests
from datetime import datetime

class VersionManager:
    """
    Motor de Atualização Universal v1.0
    Arquitetura Sênior: Desacoplada, Resiliente e Segura.
    """
    
    def __init__(self, repo_owner, repo_name, current_version_file="version.json"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.version_file = current_version_file
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        self.timeout = 10 # Segundos para timeout de rede

    def get_local_info(self):
        """Retorna o dicionário completo da versão local."""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {"version": "0.0.0"}
        except Exception:
            return {"version": "0.0.0"}

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
                
                # Engenharia Sênior: Comparação de versão
                has_update = remote_version != local_version
                
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
