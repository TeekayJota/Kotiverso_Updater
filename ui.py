import os
import threading
import requests
import customtkinter as ctk
import core
import prerequisites
from dotenv import load_dotenv
load_dotenv()

URL_INDEX = os.getenv("URL_INDEX")

class Aplicacion(ctk.CTk):
    def al_cambiar_perfil(self, seleccion):
        """Resetea la UI cuando el usuario cambia de perfil."""
        # Devolvemos el botón a su estado y color original azul
        self.btn_accion.configure(
            text="Sincronizar Entorno", state="normal", 
            fg_color=("#3B8ED0", "#1F6AA5"), hover_color=("#36719F", "#144870")
        )
        self.lbl_titulo.configure(text="Kotiverso Cloud")
        self.lbl_estado.configure(text="Listo para iniciar.", text_color="gray")
        self.barra_progreso.set(0)
        self.barra_progreso.pack_forget()

    def __init__(self):
        super().__init__()
        self.title("Kotiverso Manager")
        self.geometry("460x490") # Le di un pelín más de altura para que respiren los elementos
        self.resizable(False, False)
        
        # Tema general oscuro y acentos azules
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.perfiles_data = {}
        self.launchers_encontrados = {}

        # --- CABECERA ---
        self.lbl_titulo = ctk.CTkLabel(self, text="Estableciendo conexión...", font=("Helvetica", 22, "bold"))
        self.lbl_titulo.pack(pady=(25, 2))

        self.lbl_subtitulo = ctk.CTkLabel(self, text="Sincronizador de Modpacks", font=("Helvetica", 12), text_color="gray")
        self.lbl_subtitulo.pack(pady=(0, 15))

        # --- PANEL DE PERFILES (Dropdown estandarizado a 350px) ---
        self.selector_perfil = ctk.CTkOptionMenu(
            self, values=["Cargando nube..."], 
            command=self.al_cambiar_perfil,
            width=350, height=35, # <--- Estandarizado al ancho de la barra
            font=("Helvetica", 13, "bold"),
            fg_color="#3b3b3b", button_color="#2b2b2b", dropdown_fg_color="#2b2b2b"
        )
        self.selector_perfil.pack(pady=10)

        # --- TARJETA DE OPCIONES (Frame) ---
        self.frame_opciones = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        # Al poner padx=55 en una ventana de 460, el frame medirá exactamente 350px de ancho
        self.frame_opciones.pack(pady=10, padx=55, fill="x")

        # Metemos los switches DENTRO del frame y los CENTRAMOS (borramos anchor="w")
        self.sw_turbo = ctk.CTkSwitch(self.frame_opciones, text="Modo Turbo (Fibra Óptica)", font=("Helvetica", 11))
        self.sw_turbo.pack(pady=(15, 5)) # <--- Sin anchor="w" se centra solo
        self.sw_turbo.select()

        self.chk_shaders = ctk.CTkCheckBox(self.frame_opciones, text="Incluir Shaders (en necesario GPU)", font=("Helvetica", 11))
        self.chk_shaders.pack(pady=(5, 15)) # <--- Sin anchor="w" se centra solo

        # --- SECCIÓN DE LAUNCHERS (Invisible y Estilizada) ---
        self.lbl_select_launcher = ctk.CTkLabel(self, text="Launcher detectado:", font=("Helvetica", 11), text_color="gray")
        # Le quitamos el fondo (fg_color="transparent") y el borde para que sea súper minimalista
        self.dropdown_launchers = ctk.CTkOptionMenu(
            self, values=["Buscando..."], width=150, height=25, 
            font=("Helvetica", 11, "bold"), fg_color="#1f1f1f", button_color="#1f1f1f", dropdown_fg_color="#2b2b2b"
        )
        self.lbl_select_launcher.pack_forget()
        self.dropdown_launchers.pack_forget()

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
        
        self.lbl_estado = ctk.CTkLabel(self, text="Listo para iniciar.", font=("Helvetica", 12), text_color="gray")
        self.lbl_estado.pack(pady=(5, 10))

        threading.Thread(target=self.cargar_perfiles, daemon=True).start()

    def cargar_perfiles(self):
        try:
            r = requests.get(URL_INDEX, timeout=10)
            datos = r.json()
            nombres = [p["nombre"] for p in datos["perfiles"]]
            for p in datos["perfiles"]: self.perfiles_data[p["nombre"]] = p
            
            self.selector_perfil.configure(values=nombres)
            self.selector_perfil.set(nombres[0])
            self.lbl_titulo.configure(text="Kotiverso Cloud")
            self.btn_accion.configure(state="normal")
            self.detectar_launchers()
        except:
            self.lbl_estado.configure(text="❌ Error: Sin respuesta de Cloudflare", text_color="red")

    def detectar_launchers(self):
        """Escanea la PC buscando ejecutables conocidos."""
        rutas = {
            "TLauncher": os.path.join(os.getenv('APPDATA'), ".minecraft", "TLauncher.exe"),
            "Minecraft Oficial": os.path.join(os.getenv('LOCALAPPDATA'), "MinecraftLauncher", "MinecraftLauncher.exe"),
            "SKLauncher": os.path.join(os.getenv('APPDATA'), ".minecraft", "sklauncher.exe"),
            "Prism Launcher": os.path.join(os.getenv('APPDATA'), "PrismLauncher", "PrismLauncher.exe")
        }
        
        self.launchers_encontrados = {n: r for n, r in rutas.items() if os.path.exists(r)}
        
        # Si hay más de uno, mostramos el selector discretamente
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
        """Muestra el progreso real y el tiempo restante."""
        self.lbl_estado.configure(text=msg)
        self.barra_progreso.set(porcentaje)
        
        m, s = divmod(eta, 60)
        tiempo = f"{m}m {s}s" if m > 0 else f"{s}s"
        self.lbl_titulo.configure(text=f"{int(porcentaje*100)}% - ETA: {tiempo}")

    def ejecutar_sincro(self):
        sel = self.selector_perfil.get()
        datos = self.perfiles_data[sel]
        hilos_finales = 8 if self.sw_turbo.get() == 1 else 4
        
        # 1. Requisitos
        prerequisites.preparar_entorno(self.actualizar_progreso)
        
        # 2. Perfil
        self.lbl_estado.configure(text="🔄 Protegiendo archivos locales...", text_color="gray")
        core.cambiar_perfil(datos["id"])
        
        # 3. Descarga (CAPTURAMOS EL RESULTADO AQUÍ)
        exito = True  # <--- CAMBIO: Asumimos éxito por defecto

        # Leemos si la casilla está marcada (1) o desmarcada (0)
        quiere_shaders = bool(self.chk_shaders.get())

        if datos.get("manifest_url"):
            exito = core.sincronizar_archivos(
                datos["manifest_url"], 
                callback_ui=self.actualizar_progreso,
                hilos=hilos_finales,
                descargar_shaders=quiere_shaders
            )

        # 4. Lógica de Finalización
        self.barra_progreso.stop()
        if exito:
            # TODO SALIÓ BIEN
            self.lbl_titulo.configure(text="¡Sincronización Completa!")
            self.lbl_estado.configure(text="✨ Todo actualizado. ¡A jugar!", text_color="green")
            self.barra_progreso.set(1)
            self.btn_accion.configure(text="¡INICIAR JUEGO!", state="normal", fg_color="#28a745", hover_color="#218838")
        else:
            # HUBO UN ERROR (Timeout, etc.)
            self.lbl_titulo.configure(text="Sincronización Fallida")
            self.lbl_estado.configure(text="❌ Error de conexión. Revisa tu internet y reintenta.", text_color="#ff4444")
            self.barra_progreso.set(0) # Reseteamos barra
            self.btn_accion.configure(text="Reintentar Sincronización", state="normal", fg_color="#3b3b3b", hover_color="#4b4b4b")

    def lanzar_game(self):
        if len(self.launchers_encontrados) > 1:
            ruta = self.launchers_encontrados[self.dropdown_launchers.get()]
        elif len(self.launchers_encontrados) == 1:
            ruta = list(self.launchers_encontrados.values())[0]
        else:
            ruta = os.path.join(os.getenv('APPDATA'), ".minecraft", "TLauncher.exe")

        try:
            os.startfile(ruta)
            self.after(2000, self.destroy)
        except:
            self.lbl_estado.configure(text="❌ No se pudo abrir el launcher automáticamente.", text_color="red")

if __name__ == "__main__":
    app = Aplicacion()
    app.mainloop()