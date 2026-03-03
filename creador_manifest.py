import os
import hashlib
import json
from dotenv import load_dotenv

# Cargamos el .env para obtener las rutas locales
load_dotenv()

# Ruta al index que ahora vive en la carpeta del manager
RUTA_INDEX_LOCAL = "index.json"
RUTA_CARPETA_MINECRAFT = os.getenv("LOCAL_RUTA_DATOS_MC")

def obtener_hash(ruta):
    """Genera un hash SHA256 del archivo para verificar integridad."""
    sha256 = hashlib.sha256()
    try:
        with open(ruta, "rb") as f:
            for bloque in iter(lambda: f.read(4096), b""):
                sha256.update(bloque)
        return sha256.hexdigest()
    except Exception as e:
        print(f"❌ Error al hashear {ruta}: {e}")
        return None

def generar_manifest():
    # 1. Verificar existencia del Index
    if not os.path.exists(RUTA_INDEX_LOCAL):
        print(f"❌ ERROR: No se encuentra '{RUTA_INDEX_LOCAL}' en la carpeta del script.")
        return

    # 2. Cargar el index para sacar la configuración de los packs
    with open(RUTA_INDEX_LOCAL, "r", encoding="utf-8") as f:
        datos_index = json.load(f)
    
    packs = {p["id"]: p for p in datos_index["modpacks"]}
    
    print("\n--- GENERADOR DE MANIFEST ---")
    print("Packs configurados en index.json:")
    for pid in packs.keys():
        print(f" > {pid}")
    
    eleccion = input("\n¿Para qué pack quieres generar el manifest? (ID): ").lower()

    if eleccion not in packs:
        print(f"❌ '{eleccion}' no es un ID válido en el index.json")
        return

    pack = packs[eleccion]
    url_base = pack["url_base_cloud"]
    version_pack = pack.get("version_pack", "1.0.0")

    if not RUTA_CARPETA_MINECRAFT or not os.path.exists(RUTA_CARPETA_MINECRAFT):
        print(f"❌ ERROR: La ruta local '{RUTA_CARPETA_MINECRAFT}' no es válida. Revisa tu .env")
        return

    print(f"\n🔍 Analizando archivos para: {eleccion.upper()} (v{version_pack})")
    print(f"📂 Carpeta origen: {RUTA_CARPETA_MINECRAFT}")
    
    archivos_data = {}
    
    # 3. Escaneo de archivos
    for raiz, _, archivos in os.walk(RUTA_CARPETA_MINECRAFT):
        for nombre_archivo in archivos:
            ruta_completa = os.path.join(raiz, nombre_archivo)
            # Calculamos la ruta relativa (ej: mods/test.jar)
            ruta_relativa = os.path.relpath(ruta_completa, RUTA_CARPETA_MINECRAFT)
            # IMPORTANTE: Forzar el separador '/' para compatibilidad con Web y Linux
            ruta_web = ruta_relativa.replace("\\", "/")
            
            f_hash = obtener_hash(ruta_completa)
            if f_hash:
                archivos_data[ruta_web] = {
                    "hash": f_hash,
                    "size": os.path.getsize(ruta_completa),
                    "url": f"{url_base}/{ruta_web}" # URL generada dinámicamente
                }
                print(f"✔️ {ruta_web}")

    # 4. Guardar el archivo final
    manifest = {
        "version": version_pack,
        "pack_id": eleccion,
        "files": archivos_data
    }

    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"\n🎉 ¡manifest.json para '{eleccion}' creado con éxito!")
    print("Recuerda subirlo a la nube usando 'subidor_nube.py'.")

if __name__ == "__main__":
    generar_manifest()