import os
import subprocess
import requests
import tempfile
import time
from dotenv import load_dotenv

load_dotenv()

def verificar_java_en_directorio(version_buscada):
    """
    Busca el ejecutable de Java en rutas comunes de instalación sin depender del PATH.
    """
    version_str = str(version_buscada)
    # Rutas donde Windows suele instalar Java
    rutas_busqueda = [
        os.environ.get('ProgramFiles', r'C:\Program Files'),
        os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs')
    ]
    
    # Prefijos comunes de carpetas de Java
    prefijos = ["Java", "Eclipse Adoptium", "Microsoft", "BellSoft", "Zulu"]

    for base in rutas_busqueda:
        for prefijo in prefijos:
            ruta_padre = os.path.join(base, prefijo)
            if os.path.exists(ruta_padre):
                try:
                    for carpeta in os.listdir(ruta_padre):
                        # Buscamos carpetas que contengan el número de versión (ej: jdk-17 o jre1.8)
                        if (version_str == "8" and ("1.8" in carpeta or "jre8" in carpeta)) or \
                           (f"-{version_str}" in carpeta or f"{version_str}." in carpeta or carpeta.endswith(version_str)):
                            
                            ruta_java = os.path.join(ruta_padre, carpeta, "bin", "java.exe")
                            if os.path.exists(ruta_java):
                                # Verificación final: preguntar al binario su versión real
                                res = subprocess.run([ruta_java, '-version'], capture_output=True, text=True)
                                if version_str == "8" and 'version "1.8' in res.stderr: return True
                                if f'version "{version_str}' in res.stderr: return True
                except:
                    continue
    return False

def preparar_entorno(version_requerida, url_descarga, callback_ui):
    version_str = str(version_requerida)
    if callback_ui: callback_ui(f"🔍 Verificando Java {version_str}...", 0, 0)
    
    # --- NIVEL 1: Verificar PATH Global (Consola) ---
    try:
        resultado = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=5)
        output = resultado.stderr.lower()
        if (version_str == "8" and 'version "1.8' in output) or (f'version "{version_str}' in output):
            if callback_ui: callback_ui(f"✓ Java {version_str} (Sistema) detectado", 1, 0)
            return True
    except: pass

    # --- NIVEL 2: Búsqueda Profunda en Disco (Carpetas de Instalación) ---
    if callback_ui: callback_ui(f"🔎 Buscando Java {version_str} en el disco...", 0.3, 0)
    if verificar_java_en_directorio(version_requerida):
        if callback_ui: callback_ui(f"✓ Java {version_str} hallado en archivos de programa", 1, 0)
        return True

    # --- NIVEL 3: DESCARGA E INSTALACIÓN (Si nada de lo anterior funcionó) ---
    if not url_descarga:
        if callback_ui: callback_ui(f"❌ Error: Java {version_str} no hallado y sin URL", 0, 0)
        return False

    ruta_msi = os.path.join(tempfile.gettempdir(), f"java{version_str}_installer.msi")
    
    try:
        if callback_ui: callback_ui(f"⬇️ Descargando Java {version_str}...", 0.4, 0)
        with requests.get(url_descarga, stream=True, timeout=20) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            descargado = 0
            inicio = time.time()
            with open(ruta_msi, 'wb') as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        descargado += len(chunk)
                        if callback_ui and total_size > 0:
                            porc = descargado / total_size
                            transcurrido = time.time() - inicio
                            vel = descargado / transcurrido if transcurrido > 0 else 0
                            eta = int((total_size - descargado) / vel) if vel > 0 else 0
                            callback_ui(f"⬇️ Bajando Java {version_str}...", porc, eta)
    except Exception as e:
        if callback_ui: callback_ui(f"❌ Error descarga: {str(e)}", 0, 0)
        return False
            
    if callback_ui: callback_ui(f"⚡ Instalando Java {version_str}...", 1, 0)
    try:
        # Instalación silenciosa
        subprocess.run(['msiexec.exe', '/i', ruta_msi, '/quiet', '/norestart', '/qn'], check=True)
        try: os.remove(ruta_msi)
        except: pass
        if callback_ui: callback_ui(f"✓ Java {version_str} instalado con éxito", 1, 0)
        time.sleep(3) 
        return True
    except:
        if callback_ui: callback_ui("❌ Error en la instalación silenciosa", 0, 0)
        return False