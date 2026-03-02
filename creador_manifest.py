import os
import hashlib
import json
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DESDE ENTORNO ---
RUTA_CARPETA_MINECRAFT = os.getenv("LOCAL_RUTA_DATOS_MC")
URL_BASE_CLOUD = os.getenv("URL_BASE_CLOUD")
VERSION_MODPACK = "1.0.0"

def obtener_hash(ruta):
    sha256 = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(4096), b""):
            sha256.update(bloque)
    return sha256.hexdigest()

def generar_manifest():
    if not RUTA_CARPETA_MINECRAFT:
        print("❌ Error: RUTA_CARPETA_MINECRAFT no definida en .env")
        return

    print(f"🔍 Analizando carpeta: {RUTA_CARPETA_MINECRAFT}")
    archivos_data = {}
    
    for raiz, _, archivos in os.walk(RUTA_CARPETA_MINECRAFT):
        for archivo in archivos:
            ruta_completa = os.path.join(raiz, archivo)
            ruta_relativa = os.path.relpath(ruta_completa, RUTA_CARPETA_MINECRAFT)
            ruta_web = ruta_relativa.replace("\\", "/")
            
            archivos_data[ruta_web] = {
                "hash": obtener_hash(ruta_completa),
                "size": os.path.getsize(ruta_completa),
                "url": f"{URL_BASE_CLOUD}/{ruta_web}"
            }
            print(f"✔️ Procesado: {ruta_web}")

    manifest = {"version": VERSION_MODPACK, "files": archivos_data}

    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    print("🎉 ¡manifest.json creado con éxito!")

if __name__ == "__main__":
    generar_manifest()