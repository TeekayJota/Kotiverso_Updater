import os
import subprocess
import requests
import tempfile
import time
from dotenv import load_dotenv
load_dotenv()

URL_JAVA = os.getenv("URL_JAVA")

def preparar_entorno(callback_ui):
    # --- VERIFICACIÓN ---
    if callback_ui: callback_ui("🔍 Verificando Java 21...", 0, 0)
    
    java_ok = False
    try:
        resultado = subprocess.run(['java', '-version'], capture_output=True, text=True, check=True)
        if "version \"21" in resultado.stderr:
            java_ok = True
            if callback_ui: callback_ui("✓ Java 21 detectado", 1, 0)
    except: pass

    if not java_ok:
        ruta_java = os.path.join(tempfile.gettempdir(), "java21_kotomi.msi")
        
        # --- DESCARGA CON PROGRESO Y ETA ---
        with requests.get(URL_JAVA, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            descargado = 0
            inicio = time.time()
            
            with open(ruta_java, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        descargado += len(chunk)
                        
                        # Cálculo de progreso
                        if callback_ui and total_size > 0:
                            porcentaje = descargado / total_size
                            transcurrido = time.time() - inicio
                            velocidad = descargado / transcurrido if transcurrido > 0 else 0
                            eta = int((total_size - descargado) / velocidad) if velocidad > 0 else 0
                            callback_ui("⬇️ Descargando Java 21...", porcentaje, eta)
            
        if callback_ui: callback_ui("⚡ Instalando Java (Silencioso)...", 1, 0)
        subprocess.run(['msiexec.exe', '/i', ruta_java, '/quiet', '/norestart'], check=True)
        if callback_ui: callback_ui("✓ Java 21 instalado", 1, 0)

    return True