import pygame
import math
import threading
import time
from enum import Enum
from typing import List, Tuple

# Colores mejorados para mejor legibilidad
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
VERDE = (34, 139, 34)  # Verde más oscuro
AZUL = (25, 25, 112)   # Azul marino
AMARILLO = (255, 215, 0)
ROJO = (220, 20, 60)
VERDE_CLARO = (152, 251, 152)  # Verde menta claro
AZUL_CLARO = (230, 240, 255)   # Azul muy claro
GRIS_CLARO = (248, 248, 255)   # Casi blanco
GRIS_TEXTO = (64, 64, 64)      # Gris oscuro para texto
MORADO = (75, 0, 130)

class FaseTutorial(Enum):
    INICIO = 0
    INTERFAZ_BASICA = 1
    COLOCAR_TORRE = 2
    TIPOS_TORRES = 3
    PRIMER_ENEMIGO = 4
    RECURSOS_DINERO = 5
    TIPOS_ENEMIGOS = 6
    ESTRATEGIA = 7
    OLEADAS = 8
    VICTORIA = 9

class ObjetivoTutorial:
    def __init__(self, descripcion: str, completado: bool = False):
        self.descripcion = descripcion
        self.completado = completado

    def completar(self):
        self.completado = True

class TutorialInteractivo:
    def __init__(self, juego_principal):
        self.juego = juego_principal
        self.activo = False
        self.fase_actual = FaseTutorial.INICIO
        
        # Fuentes optimizadas para legibilidad
        self.fuente_titulo = pygame.font.SysFont("arial", 16, bold=True)
        self.fuente_texto = pygame.font.SysFont("arial", 13)
        self.fuente_pequeña = pygame.font.SysFont("arial", 12)
        
        self.objetivos_actuales: List[ObjetivoTutorial] = []
        self.mensaje_principal = ""
        self.mensaje_secundario = ""
        self.puede_continuar = False
        self.torres_colocadas_inicial = 0
        self.enemigos_tutorial_spawneados = 0
        self.tiempo_fase_inicio = 0
        
        # SIMPLIFICADO: Solo contar torres totales
        self.contador_torres_fase = 0

    def iniciar_tutorial(self):
        self.activo = True
        self.fase_actual = FaseTutorial.INICIO
        self.juego.gestor_recursos.recursos = {"dinero": 500, "vidas": 10}  # Más dinero
        self.juego.torres.clear()
        self.juego.enemigos.clear()
        self.juego.proyectiles.clear()
        self.torres_colocadas_inicial = 0
        self.enemigos_tutorial_spawneados = 0
        self.tiempo_fase_inicio = pygame.time.get_ticks()
        self.contador_torres_fase = 0
        self._cargar_fase()

    def _cargar_fase(self):
        self.objetivos_actuales.clear()
        self.puede_continuar = False
        self.tiempo_fase_inicio = pygame.time.get_ticks()
        
        # Resetear contador al entrar a fase de torres
        if self.fase_actual == FaseTutorial.TIPOS_TORRES:
            self.contador_torres_fase = len(self.juego.torres)
        
        print(f"DEBUG: ========== CARGANDO FASE {self.fase_actual} ==========")
        
        if self.fase_actual == FaseTutorial.INICIO:
            self.mensaje_principal = "¡Bienvenido al Tutorial!"
            self.mensaje_secundario = "Aprende Defense Zone 3 HD paso a paso"
            self.objetivos_actuales.append(ObjetivoTutorial("Presiona ESPACIO para comenzar"))
            
        elif self.fase_actual == FaseTutorial.INTERFAZ_BASICA:
            self.mensaje_principal = "Interfaz del Juego"
            self.mensaje_secundario = "Observa los elementos de la pantalla"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Dinero (arriba izquierda): Para torres"),
                ObjetivoTutorial("Vidas (arriba izquierda): Si llegan a 0, pierdes"),
                ObjetivoTutorial("Teclas 1,2,3: Tipos de torre")
            ])
            
        elif self.fase_actual == FaseTutorial.COLOCAR_TORRE:
            self.mensaje_principal = "Coloca tu Primera Torre"
            self.mensaje_secundario = "Presiona '1' para Torre Cañón, luego clic"
            self.objetivos_actuales.append(ObjetivoTutorial("Coloca una Torre Cañón ($50)"))
            self.torres_colocadas_inicial = len(self.juego.torres)
            
        elif self.fase_actual == FaseTutorial.TIPOS_TORRES:
            self.mensaje_principal = "Experimenta con Torres"
            self.mensaje_secundario = "Coloca 2 torres más para experimentar"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Coloca otra torre (cualquier tipo)"),
                ObjetivoTutorial("Coloca una tercera torre")
            ])
            self.contador_torres_fase = len(self.juego.torres)
            print(f"DEBUG: Iniciando fase torres con {self.contador_torres_fase} torres existentes")
            
        elif self.fase_actual == FaseTutorial.PRIMER_ENEMIGO:
            self.mensaje_principal = "¡Tu Primer Enemigo!"
            self.mensaje_secundario = "Las torres atacan automáticamente"
            self.objetivos_actuales.append(ObjetivoTutorial("Observa cómo tu torre dispara"))
            self._generar_enemigo_tutorial('basico')
            
        elif self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            self.mensaje_principal = "Gestión de Recursos"
            self.mensaje_secundario = "Ganas dinero eliminando enemigos"
            dinero_actual = self.juego.gestor_recursos.obtener('dinero')
            self.objetivos_actuales.extend([
                ObjetivoTutorial(f"Dinero actual: ${dinero_actual}"),
                ObjetivoTutorial("Cada enemigo da dinero al morir"),
                ObjetivoTutorial("Usa el dinero para más torres")
            ])
            
        elif self.fase_actual == FaseTutorial.TIPOS_ENEMIGOS:
            self.mensaje_principal = "Tipos de Enemigos"
            self.mensaje_secundario = "Diferentes enemigos, estrategias diferentes"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Rojos: Básicos (50 HP, velocidad normal)"),
                ObjetivoTutorial("Amarillos: Rápidos (30 HP, veloces)"),
                ObjetivoTutorial("Grises: Tanques (120 HP, lentos, duros)")
            ])
            self._generar_enemigos_variados()
            
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            self.mensaje_principal = "Estrategia Básica"
            self.mensaje_secundario = "Observa cómo funcionan las torres juntas"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Las torres se complementan entre sí"),
                ObjetivoTutorial("Diferentes torres para diferentes enemigos"),
                ObjetivoTutorial("Posicionamiento estratégico")
            ])
            
        elif self.fase_actual == FaseTutorial.OLEADAS:
            self.mensaje_principal = "¡Oleada de Enemigos!"
            self.mensaje_secundario = "Defiende contra múltiples enemigos"
            self.objetivos_actuales.append(ObjetivoTutorial("Sobrevive a la oleada tutorial"))
            self._iniciar_oleada_tutorial()
            
        elif self.fase_actual == FaseTutorial.VICTORIA:
            self.mensaje_principal = "¡Tutorial Completado!"
            self.mensaje_secundario = "Ya dominas lo básico del juego"
            self.objetivos_actuales.append(ObjetivoTutorial("Presiona ESC para volver al menú"))

    def _generar_enemigo_tutorial(self, tipo: str):
        try:
            from Enemigo import EnemigoBasico, EnemigoRapido, EnemigoTanque
            clases_enemigos = {
                'basico': EnemigoBasico,
                'rapido': EnemigoRapido,
                'tanque': EnemigoTanque
            }
            if tipo in clases_enemigos and len(self.juego.camino) > 0:
                enemigo = clases_enemigos[tipo](self.juego.camino[0][0], self.juego.camino[0][1])
                enemigo.ruta = self.juego.camino
                self.juego.enemigos.append(enemigo)
                self.enemigos_tutorial_spawneados += 1
                print(f"DEBUG: Enemigo {tipo} generado. Total enemigos: {len(self.juego.enemigos)}")
        except Exception as e:
            print(f"Error generando enemigo tutorial: {e}")
            # Si hay error, marcar objetivo como completado para continuar
            if self.objetivos_actuales:
                self.objetivos_actuales[0].completar()

    def _generar_enemigos_variados(self):
        tipos = ['basico', 'rapido', 'tanque']
        try:
            from Enemigo import EnemigoBasico, EnemigoRapido, EnemigoTanque
            clases_enemigos = {
                'basico': EnemigoBasico,
                'rapido': EnemigoRapido,
                'tanque': EnemigoTanque
            }
            for i, tipo in enumerate(tipos):
                if tipo in clases_enemigos and len(self.juego.camino) > 0:
                    x = self.juego.camino[0][0] - (i * 60)
                    enemigo = clases_enemigos[tipo](x, self.juego.camino[0][1])
                    enemigo.ruta = self.juego.camino
                    self.juego.enemigos.append(enemigo)
        except Exception as e:
            print(f"Error generando enemigos variados: {e}")

    def _iniciar_oleada_tutorial(self):
        def generar_oleada():
            tipos = ['basico', 'basico', 'rapido', 'basico']
            try:
                from Enemigo import EnemigoBasico, EnemigoRapido, EnemigoTanque
                clases_enemigos = {
                    'basico': EnemigoBasico,
                    'rapido': EnemigoRapido,
                    'tanque': EnemigoTanque
                }
                for i, tipo in enumerate(tipos):
                    time.sleep(1.0)
                    if self.activo and self.fase_actual == FaseTutorial.OLEADAS:
                        if tipo in clases_enemigos and len(self.juego.camino) > 0:
                            enemigo = clases_enemigos[tipo](self.juego.camino[0][0], self.juego.camino[0][1])
                            enemigo.ruta = self.juego.camino
                            self.juego.enemigos.append(enemigo)
                            print(f"DEBUG: Enemigo oleada {tipo} agregado")
            except Exception as e:
                print(f"Error en oleada tutorial: {e}")
        
        hilo = threading.Thread(target=generar_oleada)
        hilo.daemon = True
        hilo.start()

    def actualizar(self, dt: float):
        if not self.activo:
            return
        
        self._verificar_objetivos()
        
        # Verificar si puede continuar
        self.puede_continuar = all(obj.completado for obj in self.objetivos_actuales)
        
        # AUTO-AVANCE INMEDIATO para la fase de torres
        if self.fase_actual == FaseTutorial.TIPOS_TORRES and self.puede_continuar:
            print("DEBUG: ¡AVANZANDO INMEDIATAMENTE DESDE TIPOS TORRES!")
            pygame.time.wait(500)  # Pequeña pausa para que el usuario vea
            self._avanzar_fase()
            return
        
        # Auto-avance para otras fases
        tiempo_transcurrido = pygame.time.get_ticks() - self.tiempo_fase_inicio
        if tiempo_transcurrido > 10000:  # 10 segundos máximo por fase
            print(f"DEBUG: Auto-avance por tiempo excedido en fase {self.fase_actual}")
            for objetivo in self.objetivos_actuales:
                objetivo.completar()
            self.puede_continuar = True

    def _verificar_objetivos(self):
        tiempo_transcurrido = pygame.time.get_ticks() - self.tiempo_fase_inicio
        
        if self.fase_actual == FaseTutorial.INTERFAZ_BASICA:
            if tiempo_transcurrido > 1500:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.COLOCAR_TORRE:
            torres_actuales = len(self.juego.torres)
            if torres_actuales > self.torres_colocadas_inicial:
                self.objetivos_actuales[0].completar()
                print(f"DEBUG: Torre colocada! {torres_actuales} torres totales")
            elif tiempo_transcurrido > 8000:
                self.objetivos_actuales[0].completar()
                print("DEBUG: Auto-completando colocación de torre por tiempo")
                
        elif self.fase_actual == FaseTutorial.TIPOS_TORRES:
            torres_actuales = len(self.juego.torres)
            torres_nuevas = torres_actuales - self.contador_torres_fase
            
            print(f"DEBUG: Torres actuales: {torres_actuales}, Al inicio de fase: {self.contador_torres_fase}, Nuevas: {torres_nuevas}")
            
            # Marcar objetivos según torres nuevas colocadas
            if torres_nuevas >= 1:
                self.objetivos_actuales[0].completar()
                print("DEBUG: ¡Objetivo 1 completado! (primera torre nueva)")
            if torres_nuevas >= 2:
                self.objetivos_actuales[1].completar()
                print("DEBUG: ¡Objetivo 2 completado! (segunda torre nueva)")
                print("DEBUG: ¡TODOS LOS OBJETIVOS DE TORRES COMPLETADOS!")
            
            # Fallback por tiempo
            if tiempo_transcurrido > 6000:
                print("DEBUG: Auto-completando tipos de torres por tiempo")
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.PRIMER_ENEMIGO:
            enemigos_activos = sum(1 for e in self.juego.enemigos if hasattr(e, 'activo') and e.activo)
            if self.enemigos_tutorial_spawneados > 0 and enemigos_activos == 0:
                self.objetivos_actuales[0].completar()
                print("DEBUG: Primer enemigo eliminado")
            elif tiempo_transcurrido > 8000:
                self.objetivos_actuales[0].completar()
                print("DEBUG: Auto-completando primer enemigo por tiempo")
                
        elif self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            if tiempo_transcurrido > 2000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.TIPOS_ENEMIGOS:
            if tiempo_transcurrido > 3000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            if tiempo_transcurrido > 3000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.OLEADAS:
            enemigos_activos = sum(1 for e in self.juego.enemigos if hasattr(e, 'activo') and e.activo)
            if enemigos_activos == 0 and tiempo_transcurrido > 3000:
                self.objetivos_actuales[0].completar()
                print("DEBUG: Oleada tutorial completada")

    def manejar_evento(self, evento) -> bool:
        if not self.activo:
            return False
            
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_SPACE:
                print("DEBUG: ESPACIO presionado")
                if self.puede_continuar or self.fase_actual == FaseTutorial.INICIO:
                    self._avanzar_fase()
                    return True
                else:
                    # FUERZA avance en cualquier caso
                    print("DEBUG: FORZANDO avance con ESPACIO")
                    self._avanzar_fase()
                    return True
                    
            elif evento.key == pygame.K_TAB:
                print(f"DEBUG MANUAL - Estado completo:")
                print(f"  Fase: {self.fase_actual}")
                print(f"  Torres totales: {len(self.juego.torres)}")
                print(f"  Puede continuar: {self.puede_continuar}")
                print(f"  Objetivos: {[(i, obj.descripcion, obj.completado) for i, obj in enumerate(self.objetivos_actuales)]}")
                
                if self.fase_actual == FaseTutorial.TIPOS_TORRES:
                    print(f"  Torres al inicio de fase: {self.contador_torres_fase}")
                    print(f"  Torres nuevas: {len(self.juego.torres) - self.contador_torres_fase}")
                
                # FORZAR completado
                print("  FORZANDO COMPLETADO DE TODOS LOS OBJETIVOS")
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                return True
                
            elif evento.key == pygame.K_ESCAPE:
                self._salir_tutorial()
                return True
                    
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.puede_continuar:
                self._avanzar_fase()
                return True
                
        return False

    def _avanzar_fase(self):
        try:
            from Main import EstadoJuego
            fases = list(FaseTutorial)
            indice_actual = fases.index(self.fase_actual)
            if indice_actual < len(fases) - 1:
                fase_anterior = self.fase_actual
                self.fase_actual = fases[indice_actual + 1]
                print(f"DEBUG: =======================================")
                print(f"DEBUG: AVANZANDO DE {fase_anterior} A {self.fase_actual}")
                print(f"DEBUG: =======================================")
                self._cargar_fase()
            else:
                self._salir_tutorial()
        except Exception as e:
            print(f"Error avanzando fase: {e}")
            self._salir_tutorial()

    def _salir_tutorial(self):
        try:
            from Main import EstadoJuego
            self.activo = False
            self.juego.estado_juego = EstadoJuego.MENU
            print("DEBUG: =======================================")
            print("DEBUG: SALIENDO DEL TUTORIAL")
            print("DEBUG: =======================================")
        except Exception as e:
            print(f"Error saliendo del tutorial: {e}")

    def dibujar(self, pantalla: pygame.Surface):
        if not self.activo:
            return
        
        # Panel principal compacto
        panel_x = 10
        panel_y = 160
        panel_ancho = 450
        panel_alto_principal = 80
        
        panel_principal = pygame.Rect(panel_x, panel_y, panel_ancho, panel_alto_principal)
        
        # Fondo semi-transparente
        s = pygame.Surface((panel_ancho, panel_alto_principal))
        s.set_alpha(220)
        s.fill(AZUL_CLARO)
        pantalla.blit(s, (panel_x, panel_y))
        
        pygame.draw.rect(pantalla, AZUL, panel_principal, 2)
        
        # Título
        titulo = self.fuente_titulo.render(self.mensaje_principal, True, AZUL)
        pantalla.blit(titulo, (panel_x + 8, panel_y + 8))
        
        # Mensaje secundario
        if self.mensaje_secundario:
            lineas_mensaje = self._dividir_texto(self.mensaje_secundario, 50)
            y_offset = 28
            for linea in lineas_mensaje:
                mensaje = self.fuente_texto.render(linea, True, GRIS_TEXTO)
                pantalla.blit(mensaje, (panel_x + 8, panel_y + y_offset))
                y_offset += 16
        
        # Panel de objetivos
        objetivos_y = panel_y + panel_alto_principal + 5
        altura_objetivos = min(len(self.objetivos_actuales) * 18 + 30, 120)
        panel_objetivos = pygame.Rect(panel_x, objetivos_y, panel_ancho, altura_objetivos)
        
        s2 = pygame.Surface((panel_ancho, altura_objetivos))
        s2.set_alpha(200)
        s2.fill(VERDE_CLARO)
        pantalla.blit(s2, (panel_x, objetivos_y))
        
        pygame.draw.rect(pantalla, VERDE, panel_objetivos, 2)
        
        # Título objetivos
        titulo_obj = self.fuente_texto.render("Objetivos:", True, VERDE)
        pantalla.blit(titulo_obj, (panel_x + 8, objetivos_y + 6))
        
        # Lista de objetivos
        y_offset = 24
        for i, objetivo in enumerate(self.objetivos_actuales[:4]):  # Máximo 4
            color = VERDE if objetivo.completado else GRIS_TEXTO
            simbolo = "✓" if objetivo.completado else "•"
            texto = f"{simbolo} {objetivo.descripcion}"
            
            if len(texto) > 55:
                texto = texto[:52] + "..."
            
            obj_surface = self.fuente_pequeña.render(texto, True, color)
            pantalla.blit(obj_surface, (panel_x + 12, objetivos_y + y_offset))
            y_offset += 18
        
        # Indicador de continuar
        if self.puede_continuar:
            continuar_x = 1000
            continuar_y = 700
            continuar_texto = "ESPACIO: Continuar"
            
            continuar_surface = self.fuente_texto.render(continuar_texto, True, BLANCO)
            rect_continuar = continuar_surface.get_rect()
            rect_continuar.x = continuar_x
            rect_continuar.y = continuar_y
            
            # Fondo pulsante
            pulse = int(50 + 40 * math.sin(pygame.time.get_ticks() * 0.01))
            fondo_continuar = pygame.Surface((rect_continuar.width + 20, rect_continuar.height + 10))
            fondo_continuar.set_alpha(pulse + 150)
            fondo_continuar.fill(VERDE)
            
            pantalla.blit(fondo_continuar, (continuar_x - 10, continuar_y - 5))
            pygame.draw.rect(pantalla, VERDE, (continuar_x - 10, continuar_y - 5, rect_continuar.width + 20, rect_continuar.height + 10), 2)
            pantalla.blit(continuar_surface, rect_continuar)
        
        # Ayuda
        ayuda_texto = "ESPACIO: Avanzar | TAB: Debug info | ESC: Salir"
        ayuda_surface = self.fuente_pequeña.render(ayuda_texto, True, GRIS_TEXTO)
        pantalla.blit(ayuda_surface, (panel_x, 770))
        
        # INFO DE DEBUG EN PANTALLA para fase de torres
        if self.fase_actual == FaseTutorial.TIPOS_TORRES:
            debug_texto = f"DEBUG: Torres={len(self.juego.torres)} | Inicio={self.contador_torres_fase} | Nuevas={len(self.juego.torres)-self.contador_torres_fase}"
            debug_surface = self.fuente_pequeña.render(debug_texto, True, ROJO)
            pantalla.blit(debug_surface, (panel_x, 750))

    def _dividir_texto(self, texto: str, max_chars: int) -> List[str]:
        palabras = texto.split()
        lineas = []
        linea_actual = ""
        
        for palabra in palabras:
            if len(linea_actual + " " + palabra) <= max_chars:
                linea_actual += (" " if linea_actual else "") + palabra
            else:
                if linea_actual:
                    lineas.append(linea_actual)
                linea_actual = palabra
        
        if linea_actual:
            lineas.append(linea_actual)
        
        return lineas 