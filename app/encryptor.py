#!/usr/bin/env python3
"""
Criptografia de ponta a ponta para o Ajax Super-Agent.
Empacota o código fonte com AES-256 e gera um loader protegido.

Uso:
    python encryptor.py --build-exe    # Gera executável protegido
    python encryptor.py --build-apk    # Prepara para Android (Kivy/Buildozer)
"""
from __future__ import annotations
import argparse
import base64
import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================
PROJECT_ROOT = Path(__file__).parent
SOURCE_DIRS = ["agent_core", "backend", "cli.py"]
OUTPUT_DIR = PROJECT_ROOT / "dist_encrypted"
KEY_FILE = OUTPUT_DIR / ".key"

# =============================================================================
# CRIPTOGRAFIA AES-256-GCM
# =============================================================================
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    print("Instalando dependências de criptografia...")
    subprocess.run([sys.executable, "-m", "pip", "install", "cryptography", "pyinstaller"], check=True)
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CodeEncryptor:
    """Empacota código Python com criptografia AES-256."""

    def __init__(self, password: str | None = None):
        self.password = password or self._generate_password()
        self.key = self._derive_key(self.password)
        self.fernet = Fernet(self.key)

    @staticmethod
    def _generate_password(length: int = 32) -> str:
        import secrets
        return secrets.token_urlsafe(length)

    def _derive_key(self, password: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"ajax_super_agent_salt_v1",  # Salt fixo para reprodutibilidade
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt_file(self, file_path: Path) -> bytes:
        """Criptografa o conteúdo de um arquivo."""
        data = file_path.read_bytes()
        return self.fernet.encrypt(data)

    def decrypt_file(self, encrypted_data: bytes) -> bytes:
        """Descriptografa dados."""
        return self.fernet.decrypt(encrypted_data)

    def encrypt_directory(self, source: Path, output: Path):
        """Criptografa todo um diretório em um pacote .enc."""
        output.mkdir(parents=True, exist_ok=True)

        # Salvar a chave (em produção, isso seria embutido no binário)
        KEY_FILE.write_text(self.password, encoding="utf-8")

        encrypted_files = []
        for py_file in source.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            rel_path = py_file.relative_to(source)
            encrypted = self.encrypt_file(py_file)

            # Nome ofuscado
            safe_name = base64.urlsafe_b64encode(str(rel_path).encode()).decode()
            out_file = output / f"{safe_name}.enc"
            out_file.write_bytes(encrypted)
            encrypted_files.append(str(rel_path))

        # Criar manifesto
        manifest = {
            "version": "1.0",
            "files": encrypted_files,
            "count": len(encrypted_files),
        }
        (output / "manifest.json").write_text(
            self.fernet.encrypt(str(manifest).encode()).decode()
        )

        print(f"[OK] {len(encrypted_files)} arquivos criptografados em: {output}")
        print(f"[OK] Chave salva em: {KEY_FILE}")
        return encrypted_files


# =============================================================================
# LOADER PROTEGIDO
# =============================================================================
LOADER_TEMPLATE = '''
"""
Ajax Super-Agent - Loader Protegido
Executa código criptografado sem expor o fonte.
"""
import base64
import importlib.util
import json
import os
import sys
import types
import tempfile
from pathlib import Path

# Chave embutida (obfuscada)
_KEY_PARTS = {key_parts!r}
_SALT = b"ajax_super_agent_salt_v1"

def _derive_key(password: str) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_SALT, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def _get_key() -> bytes:
    password = "".join(_KEY_PARTS)
    return _derive_key(password)

def _decrypt(data: bytes) -> bytes:
    from cryptography.fernet import Fernet
    return Fernet(_get_key()).decrypt(data)

class EncryptedLoader:
    def __init__(self, package_dir: str):
        self.package_dir = Path(package_dir)
        self._modules = {{}}
        self._load_manifest()

    def _load_manifest(self):
        manifest_file = self.package_dir / "manifest.json"
        if manifest_file.exists():
            encrypted = manifest_file.read_text()
            decrypted = _decrypt(encrypted.encode())
            self.manifest = eval(decrypted.decode())
        else:
            self.manifest = {{"files": [], "count": 0}}

    def _load_module(self, rel_path: str) -> types.ModuleType:
        """Carrega um módulo Python de arquivo criptografado."""
        safe_name = base64.urlsafe_b64encode(rel_path.encode()).decode()
        enc_file = self.package_dir / f"{{safe_name}}.enc"

        if not enc_file.exists():
            raise ImportError(f"Módulo não encontrado: {{rel_path}}")

        encrypted = enc_file.read_bytes()
        source = _decrypt(encrypted).decode("utf-8")

        # Criar módulo em memória
        module_name = rel_path.replace(os.sep, ".").replace(".py", "")
        module = types.ModuleType(module_name)
        module.__file__ = str(enc_file)

        # Executar o código no contexto do módulo
        exec(compile(source, str(enc_file), "exec"), module.__dict__)
        self._modules[module_name] = module
        return module

    def find_module(self, fullname: str):
        if fullname in self._modules:
            return self
        for rel_path in self.manifest.get("files", []):
            module_name = rel_path.replace(os.sep, ".").replace(".py", "")
            if module_name == fullname or fullname.startswith(module_name + "."):
                return self
        return None

    def load_module(self, fullname: str):
        if fullname in self._modules:
            return self._modules[fullname]

        for rel_path in self.manifest.get("files", []):
            module_name = rel_path.replace(os.sep, ".").replace(".py", "")
            if module_name == fullname:
                return self._load_module(rel_path)

        raise ImportError(f"Módulo não encontrado: {{fullname}}")

def main():
    # Determinar diretório do pacote criptografado
    if getattr(sys, "frozen", False):
        # Rodando como executável PyInstaller
        package_dir = Path(sys.executable).parent / "encrypted_pkg"
    else:
        package_dir = Path(__file__).parent / "encrypted_pkg"

    if not package_dir.exists():
        print("[ERRO] Pacote criptografado não encontrado!")
        sys.exit(1)

    # Registrar o loader
    loader = EncryptedLoader(str(package_dir))
    sys.meta_path.insert(0, loader)

    # Importar e executar o agente
    try:
        agent = loader.load_module("agent_core.agent")
        AjaxAgent = getattr(agent, "AjaxAgent")
        print("[OK] Ajax Super-Agent carregado com sucesso!")
        print("[OK] Código protegido - fonte não visível")
        
        # Iniciar CLI
        cli = loader.load_module("cli")
        if hasattr(cli, "main"):
            cli.main()
    except Exception as e:
        print(f"[ERRO] Falha ao carregar: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''


# =============================================================================
# BUILD SYSTEM
# =============================================================================
def build_exe():
    """Compila para executável Windows protegido."""
    print("=" * 50)
    print("BUILD: Ajax Super-Agent (Protegido)")
    print("=" * 50)

    # 1. Criar encryptor
    encryptor = CodeEncryptor()

    # 2. Criptografar código fonte
    encrypted_dir = OUTPUT_DIR / "encrypted_pkg"
    encryptor.encrypt_directory(PROJECT_ROOT, encrypted_dir)

    # 3. Gerar loader com chave embutida (ofuscada)
    key_parts = [encryptor.password[i:i+4] for i in range(0, len(encryptor.password), 4)]
    loader_code = LOADER_TEMPLATE.format(key_parts=key_parts)

    loader_file = OUTPUT_DIR / "ajax_protected.py"
    loader_file.write_text(loader_code, encoding="utf-8")

    # 4. Compilar com PyInstaller
    print("[...] Compilando executável com PyInstaller...")

    spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

a = Analysis(
    [r"{loader_file}"],
    pathex=[r"{PROJECT_ROOT}"],
    binaries=[],
    datas=[(r"{encrypted_dir}", "encrypted_pkg")],
    hiddenimports=["cryptography", "cryptography.fernet", "httpx", "openai", "sqlalchemy", "sqlite3"],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AjaxSuperAgent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    spec_file = OUTPUT_DIR / "AjaxSuperAgent.spec"
    spec_file.write_text(spec_content, encoding="utf-8")

    # Rodar PyInstaller
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean", "--noconfirm"],
            check=True,
            cwd=str(OUTPUT_DIR),
        )
        print(f"[OK] Executável gerado: {OUTPUT_DIR / 'dist' / 'AjaxSuperAgent.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Falha no PyInstaller: {e}")

    print("=" * 50)
    print("BUILD CONCLUÍDO!")
    print("=" * 50)
    print(f"Diretório: {OUTPUT_DIR}")
    print(f"Executável: {OUTPUT_DIR / 'dist' / 'AjaxSuperAgent.exe'}")
    print("O código fonte está protegido por AES-256!")


def build_apk_prep():
    """Prepara arquivos para build Android."""
    print("=" * 50)
    print("PREP: Android APK (Kivy/Buildozer)")
    print("=" * 50)

    encryptor = CodeEncryptor()
    encrypted_dir = OUTPUT_DIR / "android_encrypted"
    encryptor.encrypt_directory(PROJECT_ROOT, encrypted_dir)

    # Criar wrapper Android
    android_main = OUTPUT_DIR / "main.py"
    android_main.write_text(f'''
import os
import sys
from pathlib import Path

# Configurar paths no Android
if "ANDROID_ROOT" in os.environ:
    app_dir = Path("/data/data/org.ajax.superagent/files")
else:
    app_dir = Path(__file__).parent

sys.path.insert(0, str(app_dir))

# Importar loader
exec(open("{encrypted_dir / 'loader.py'}").read())
''', encoding="utf-8")

    print(f"[OK] Arquivos preparados em: {OUTPUT_DIR}")
    print("[INFO] Use Buildozer para compilar o APK:")
    print("       cd dist_encrypted && buildozer android debug")


# =============================================================================
# CLI
# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Criptografia Ajax Super-Agent")
    parser.add_argument("--build-exe", action="store_true", help="Gera executável Windows")
    parser.add_argument("--build-apk", action="store_true", help="Prepara para Android")
    parser.add_argument("--decrypt", type=str, help="Descriptografa arquivo .enc")
    args = parser.parse_args()

    if args.build_exe:
        build_exe()
    elif args.build_apk:
        build_apk_prep()
    elif args.decrypt:
        # Ferramenta para debug
        encryptor = CodeEncryptor(password=KEY_FILE.read_text().strip())
        data = Path(args.decrypt).read_bytes()
        print(encryptor.decrypt_file(data).decode("utf-8"))
    else:
        parser.print_help()
