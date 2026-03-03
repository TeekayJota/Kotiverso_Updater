import os
import sys
import threading
import requests
import customtkinter as ctk
import core
import prerequisites
from dotenv import load_dotenv

# --- CONFIGURACIÓN DE IDENTIDAD ---
VERSION_LOCAL = "2.1.0"

# Carga obligatoria del .env
load_dotenv()
URL_INDEX = os.getenv("URL_INDEX")

class Aplicacion(ctk.CTk):
    def al_cambiar_perfil(self, seleccion):
        """Resetea la UI cuando el usuario cambia de perfil."""
        self.btn_accion.configure(
            text="Sincronizar Entorno", state="normal", 
            fg_color=("#3B8ED0", "#1F6AA5"), hover_color=("#36719F", "#144870")
        )
        self.lbl_titulo.configure(text="Kotiverso Cloud", text_color="white")
        self.lbl_estado.configure(text="Listo para iniciar.", text_color="gray")
        self.barra_progreso.set(0)
        self.barra_progreso.pack_forget()

    def __init__(self):
        super().__init__()
        self.title(f"Kotiverso Manager v{VERSION_LOCAL}")
        self.geometry("460x520")
        self.resizable(False, False)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.perfiles_data = {}
        self.launchers_encontrados = {}

        # --- CABECERA ---
        self.lbl_titulo = ctk.CTkLabel(self, text="Estableciendo conexión...", font=("Helvetica", 22, "bold"))
        self.lbl_titulo.pack(pady=(25, 2))

        self.lbl_subtitulo = ctk.CTkLabel(self, text="Sincronizador de Modpacks", font=("Helvetica", 12), text_color="gray")
        self.lbl_subtitulo.pack(pady=(0, 15))

        # --- PANEL DE PERFILES ---
        self.selector_perfil = ctk.CTkOptionMenu(
            self, values=["Cargando nube..."], 
            command=self.al_cambiar_perfil,
            width=350, height=35,
            font=("Helvetica", 13, "bold"),
            fg_color="#3b3b3b", button_color="#2b2b2b", dropdown_fg_color="#2b2b2b"
        )
        self.selector_perfil.pack(pady=10)

        # --- TARJETA DE OPCIONES ---
        self.frame_opciones = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.frame_opciones.pack(pady=10, padx=55, fill="x")

        self.sw_turbo = ctk.CTkSwitch(self.frame_opciones, text="Modo Turbo (Fibra Óptica)", font=("Helvetica", 11))
        self.sw_turbo.pack(pady=(15, 5))
        self.sw_turbo.select()

        self.chk_shaders = ctk.CTkCheckBox(self.frame_opciones, text="Incluir Shaders (necesita GPU)", font=("Helvetica", 11))
        self.chk_shaders.pack(pady=(5, 15))

        # --- SECCIÓN DE LAUNCHERS ---
        self.lbl_select_launcher = ctk.CTkLabel(self, text="Launcher detectado:", font=("Helvetica", 11), text_color="gray")
        self.dropdown_launchers = ctk.CTkOptionMenu(
            self, values=["Buscando..."], width=150, height=25, 
            font=("Helvetica", 11, "bold"), fg_color="#1f1f1f", button_color="#1f1f1f", dropdown_fg_color="#2b2b2b"
        )

        # --- BOTÓN DE ACCIÓN ---
        self.btn_accion = ctk.CTkButton(
            self, text="Sincronizar Entorno", width=240, height=45, corner_radius=8, font=("Helvetica", 14, "bold"),
            command=self.gestionar_boton, state="disabled"
        )
        self.btn_accion.pack(pady=(20, 10))

        # --- PROGRESS Y ESTADO ---
        self.barra_progreso = ctk.CTkProgressBar(self, width=350, height=8, corner_radius=4)
        self.barra_progreso.set(0)
        self.barra_progreso.pack_forget()
        
        self.lbl_estado = ctk.CTkLabel(self, text="Estableciendo conexión...", font=("Helvetica", 12), text_color="gray")
        self.lbl_estado.pack(pady=(5, 10))

        threading.Thread(target=self.cargar_perfiles, daemon=True).start()

    def cargar_perfiles(self):
        try:
            r = requests.get(URL_INDEX, timeout=10)
            datos = r.json()
            
            # 1. VERIFICAR ACTUALIZACIONES DEL MANAGER
            info_manager = datos.get("manager", {})
            version_nube = info_manager.get("version", VERSION_LOCAL)
            
            if version_nube > VERSION_LOCAL:
                self.lbl_titulo.configure(text="📢 Actualización Disponible", text_color="#E67E22")
                self.lbl_estado.configure(text=f"Nueva v{version_nube} lista.", text_color="#E67E22")
                
                self.btn_update = ctk.CTkButton(
                    self, text="Descargar Nueva Versión", 
                    fg_color="#D35400", hover_color="#A04000",
                    command=lambda: os.startfile(info_manager.get("url"))
                )
                self.btn_update.pack(before=self.lbl_estado, pady=5)
            else:
                self.lbl_titulo.configure(text="Kotiverso Cloud")
                self.lbl_estado.configure(text="Sistema actualizado.")

            # 2. CARGAR MODPACKS + INYECTAR OPCIÓN USER
            nombres = ["Perfil Personal (user)"]
            nombres.extend([p["nombre"] for p in datos["modpacks"]])
            
            # Datos ficticios para el perfil de usuario (restauración local)
            self.perfiles_data["Perfil Personal (user)"] = {
                "id": "user",
                "nombre": "Perfil Personal (user)",
                "manifest_url": None  # Al ser None, core.py sabrá que no hay descarga
            }
            
            for p in datos["modpacks"]: 
                self.perfiles_data[p["nombre"]] = p
            
            self.selector_perfil.configure(values=nombres)
            self.selector_perfil.set(nombres[0])
            self.btn_accion.configure(state="normal")
            self.detectar_launchers()

        except Exception as e:
            self.lbl_estado.configure(text=f"❌ Error: Sin respuesta de Cloudflare", text_color="red")

    def detectar_launchers(self):
        rutas = {
            "TLauncher": os.path.join(os.getenv('APPDATA'), ".minecraft", "TLauncher.exe"),
            "Minecraft Oficial": os.path.join(os.getenv('LOCALAPPDATA'), "MinecraftLauncher", "MinecraftLauncher.exe"),
            "SKLauncher": os.path.join(os.getenv('APPDATA'), ".minecraft", "sklauncher.exe"),
            "Prism Launcher": os.path.join(os.getenv('APPDATA'), "PrismLauncher", "PrismLauncher.exe")
        }
        self.launchers_encontrados = {n: r for n, r in rutas.items() if os.path.exists(r)}
        if len(self.launchers_encontrados) > 1:
            self.dropdown_launchers.configure(values=list(self.launchers_encontrados.keys()))
            self.dropdown_launchers.set(list(self.launchers_encontrados.keys())[0])
            self.lbl_select_launcher.pack(before=self.btn_accion)
            self.dropdown_launchers.pack(before=self.btn_accion, pady=(0, 10))

    def gestionar_boton(self):
        if self.btn_accion.cget("text") == "¡INICIAR JUEGO!":
            self.lanzar_game()
        else:
            self.btn_accion.configure(state="disabled")
            self.barra_progreso.pack(pady=5)
            threading.Thread(target=self.ejecutar_sincro, daemon=True).start()

    def actualizar_progreso(self, msg, porcentaje, eta):
        self.lbl_estado.configure(text=msg)
        self.barra_progreso.set(porcentaje)
        m, s = divmod(eta, 60)
        self.lbl_titulo.configure(text=f"{int(porcentaje*100)}% - ETA: {m}m {s}s")

    def ejecutar_sincro(self):
        sel = self.selector_perfil.get()
        datos = self.perfiles_data[sel]
        hilos_finales = 8 if self.sw_turbo.get() == 1 else 4
        
        # 1. Preparar Java (Solo si es un pack de la nube)
        if datos.get("manifest_url"):
            version_java = datos.get("java_version", "21")
            url_java_directa = datos.get("url_java") 
            
            if not prerequisites.preparar_entorno(version_java, url_java_directa, self.actualizar_progreso):
                self.lbl_estado.configure(text="❌ Error crítico en entorno Java", text_color="red")
                self.btn_accion.configure(state="normal", text="Reintentar Sincronización")
                return
        
        # 2. Sincronización de Archivos / Intercambio de Carpetas
        quiere_shaders = bool(self.chk_shaders.get())
        exito = core.sincronizar_archivos(
            datos["manifest_url"], 
            datos["id"], 
            callback_ui=self.actualizar_progreso,
            hilos=hilos_finales,
            descargar_shaders=quiere_shaders
        )

        self.barra_progreso.stop()
        if exito:
            self.lbl_titulo.configure(text="¡Sincronización Completa!", text_color="#28a745")
            self.lbl_estado.configure(text="✨ Todo actualizado. ¡A jugar!", text_color="green")
            self.barra_progreso.set(1)
            self.btn_accion.configure(text="¡INICIAR JUEGO!", state="normal", fg_color="#28a745", hover_color="#218838")
        else:
            self.lbl_titulo.configure(text="Sincronización Fallida", text_color="#ff4444")
            self.lbl_estado.configure(text="❌ Error de conexión o archivos.", text_color="#ff4444")
            self.btn_accion.configure(text="Reintentar Sincronización", state="normal", fg_color="#3b3b3b")

    def lanzar_game(self):
        if len(self.launchers_encontrados) >= 1:
            ruta = self.launchers_encontrados.get(self.dropdown_launchers.get(), list(self.launchers_encontrados.values())[0])
        else:
            ruta = os.path.join(os.getenv('APPDATA'), ".minecraft", "TLauncher.exe")
        try:
            os.startfile(ruta)
            self.after(2000, self.destroy)
        except:
            self.lbl_estado.configure(text="❌ No se pudo abrir el launcher.", text_color="red")

if __name__ == "__main__":
    app = Aplicacion()
    app.mainloop()