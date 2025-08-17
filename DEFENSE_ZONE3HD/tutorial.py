import pygame
import math
from enum import Enum
from typing import List, Dict, Optional, Tuple
from Enemigo import EnemigoBasico, EnemigoRapido, EnemigoTanque, crear_enemigo
from Excepcion_juego import ExcepcionColocacionTorre, ExcepcionRecursosInsuficientes

# Colores para el tutorial
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
VERDE = (0, 255, 0)
AZUL = (0, 100, 255)
AMARILLO = (255, 255, 0)
ROJO = (255, 0, 0)
VERDE_CLARO = (144, 238, 144)
AZUL_CLARO = (173, 216, 230)
NARANJA = (255, 165, 0)
MORADO = (128, 0, 128)

class FaseTutorial(Enum):
    """Diferentes fases del tutorial jugable"""
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

class ElementoTutorial:
    """Elemento visual del tutorial (flechas, círculos, etc.)"""
    def __init__(self, tipo: str, posicion: Tuple[int, int], 
                 texto: str = "", color: Tuple[int, int, int] = AMARILLO,
                 tamaño: int = 30, duracion: float = -1):
        self.tipo = tipo
        self.posicion = posicion
        self.texto = texto
        self.color = color
        self.tamaño = tamaño
        self.duracion = duracion
        self.tiempo_inicio = pygame.time.get_ticks()
        self.activo = True
        self.animacion_offset = 0

    def actualizar(self, dt: float):
        """Actualiza la animación del elemento"""
        if self.duracion > 0:
            tiempo_transcurrido = pygame.time.get_ticks() - self.tiempo_inicio
            if tiempo_transcurrido > self.duracion:
                self.activo = False
        
        # Animación de pulsación
        tiempo = pygame.time.get_ticks()
        self.animacion_offset = math.sin(tiempo * 0.005) * 5

    def dibujar(self, pantalla: pygame.Surface, fuente: pygame.font.Font):
        """Dibuja el elemento en pantalla"""
        if not self.activo:
            return
        
        x, y = self.posicion
        
        if self.tipo == "flecha":
            self._dibujar_flecha(pantalla, x, y + self.animacion_offset)
        elif self.tipo == "circulo":
            radio = self.tamaño + int(self.animacion_offset)
            pygame.draw.circle(pantalla, self.color, (x, y), radio, 3)
        elif self.tipo == "rectangulo":
            rect = pygame.Rect(x - self.tamaño, y - self.tamaño//2, 
                             self.tamaño*2, self.tamaño)
            pygame.draw.rect(pantalla, (*self.color, 80), rect)
            pygame.draw.rect(pantalla, self.color, rect, 3)
        elif self.tipo == "texto":
            self._dibujar_texto(pantalla, fuente, x, y)

    def _dibujar_flecha(self, pantalla: pygame.Surface, x: float, y: float):
        """Dibuja una flecha animada"""
        puntos = [
            (x, y),
            (x - 10, y - 20),
            (x - 5, y - 15),
            (x - 5, y - 30),
            (x + 5, y - 30),
            (x + 5, y - 15),
            (x + 10, y - 20)
        ]
        pygame.draw.polygon(pantalla, self.color, puntos)
        pygame.draw.polygon(pantalla, NEGRO, puntos, 2)

    def _dibujar_texto(self, pantalla: pygame.Surface, fuente: pygame.font.Font, x: int, y: int):
        """Dibuja texto con fondo"""
        texto_surface = fuente.render(self.texto, True, NEGRO)
        rect_texto = texto_surface.get_rect(center=(x, y))
        
        # Fondo del texto
        padding = 8
        fondo = rect_texto.inflate(padding*2, padding*2)
        pygame.draw.rect(pantalla, BLANCO, fondo)
        pygame.draw.rect(pantalla, self.color, fondo, 2)
        
        pantalla.blit(texto_surface, rect_texto)

class ObjetivoTutorial:
    """Representa un objetivo del tutorial"""
    def __init__(self, descripcion: str, completado: bool = False):
        self.descripcion = descripcion
        self.completado = completado
        self.tiempo_completado = 0

    def completar(self):
        """Marca el objetivo como completado"""
        if not self.completado:
            self.completado = True
            self.tiempo_completado = pygame.time.get_ticks()

class TutorialInteractivo:
    """Sistema de tutorial interactivo para Defense Zone 3 HD"""
    
    def __init__(self, juego_principal):
        self.juego = juego_principal
        self.activo = False
        self.fase_actual = FaseTutorial.INICIO
        
        # Fuentes
        self.fuente_titulo = pygame.font.SysFont("arial", 28, bold=True)
        self.fuente_texto = pygame.font.SysFont("arial", 22)
        self.fuente_pequeña = pygame.font.SysFont("arial", 18)
        
        # Estado del tutorial
        self.objetivos_actuales: List[ObjetivoTutorial] = []
        self.elementos_visuales: List[ElementoTutorial] = []
        self.mensaje_principal = ""
        self.mensaje_secundario = ""
        self.puede_continuar = False
        self.tiempo_fase = 0
        
        # Configuración específica del tutorial
        self.torres_colocadas = 0
        self.enemigos_eliminados = 0
        self.dinero_ganado = 0
        self.tipos_torres_probados = set()
        
        # Controlar spawning de enemigos
        self.enemigos_tutorial_spawneados = 0
        self.max_enemigos_por_fase = {
            FaseTutorial.PRIMER_ENEMIGO: 1,
            FaseTutorial.TIPOS_ENEMIGOS: 3,
            FaseTutorial.OLEADAS: 5
        }

    def iniciar_tutorial(self):
        """Inicia el tutorial"""
        self.activo = True
        self.fase_actual = FaseTutorial.INICIO
        
        # Configurar estado inicial del juego para el tutorial
        self.juego.gestor_recursos.recursos = {"dinero": 300, "vidas": 10}
        self.juego.torres.clear()
        self.juego.enemigos.clear()
        self.juego.proyectiles.clear()
        
        # Resetear contadores
        self.torres_colocadas = 0
        self.enemigos_eliminados = 0
        self.dinero_ganado = 0
        self.tipos_torres_probados.clear()
        self.enemigos_tutorial_spawneados = 0
        
        self._cargar_fase()

    def _cargar_fase(self):
        """Carga la configuración de la fase actual"""
        self.objetivos_actuales.clear()
        self.elementos_visuales.clear()
        self.tiempo_fase = 0
        self.puede_continuar = False
        
        if self.fase_actual == FaseTutorial.INICIO:
            self.mensaje_principal = "¡Bienvenido al Tutorial!"
            self.mensaje_secundario = "Aprenderás a defender tu base paso a paso"
            self.objetivos_actuales.append(ObjetivoTutorial("Presiona ESPACIO para continuar"))
            
        elif self.fase_actual == FaseTutorial.INTERFAZ_BASICA:
            self.mensaje_principal = "Interfaz del Juego"
            self.mensaje_secundario = "Familiarízate con los elementos básicos"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Observa tu dinero (arriba izquierda)"),
                ObjetivoTutorial("Observa tus vidas (arriba izquierda)"),
                ObjetivoTutorial("Ve las teclas de torres (arriba derecha)")
            ])
            # Completar automáticamente después de unos segundos
            
        elif self.fase_actual == FaseTutorial.COLOCAR_TORRE:
            self.mensaje_principal = "Colocando Torres"
            self.mensaje_secundario = "Presiona '1' y haz clic donde quieras colocar una torre"
            self.objetivos_actuales.append(ObjetivoTutorial("Coloca tu primera Torre Cañón ($50)"))
            # Agregar elemento visual
            self.elementos_visuales.append(
                ElementoTutorial("circulo", (400, 450), "Buen lugar para torre", VERDE)
            )
            
        elif self.fase_actual == FaseTutorial.TIPOS_TORRES:
            self.mensaje_principal = "Tipos de Torres"
            self.mensaje_secundario = "Experimenta con diferentes tipos"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Prueba Torre Cañón (Tecla 1) - $50"),
                ObjetivoTutorial("Prueba Torre Misil (Tecla 2) - $100"), 
                ObjetivoTutorial("Prueba Torre Láser (Tecla 3) - $75")
            ])
            
        elif self.fase_actual == FaseTutorial.PRIMER_ENEMIGO:
            self.mensaje_principal = "¡Primer Enemigo!"
            self.mensaje_secundario = "Observa cómo tu torre ataca automáticamente"
            self.objetivos_actuales.append(ObjetivoTutorial("Elimina al enemigo rojo"))
            self._generar_enemigo_tutorial('basico')
            
        elif self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            self.mensaje_principal = "Gestión de Recursos"
            self.mensaje_secundario = "Cada enemigo te da dinero al eliminarlo"
            self.objetivos_actuales.extend([
                ObjetivoTutorial(f"Dinero actual: ${self.juego.gestor_recursos.obtener('dinero')}"),
                ObjetivoTutorial("Elimina enemigos para ganar más dinero"),
                ObjetivoTutorial("Usa el dinero sabiamente")
            ])
            
        elif self.fase_actual == FaseTutorial.TIPOS_ENEMIGOS:
            self.mensaje_principal = "Tipos de Enemigos"
            self.mensaje_secundario = "Diferentes enemigos requieren diferentes estrategias"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Enemigo Rojo: Básico (50 HP)"),
                ObjetivoTutorial("Enemigo Amarillo: Rápido (30 HP)"),
                ObjetivoTutorial("Enemigo Gris: Tanque (120 HP)")
            ])
            self._generar_enemigos_variados()
            
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            self.mensaje_principal = "Estrategia Básica"
            self.mensaje_secundario = "Coloca torres en puntos estratégicos del camino"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Coloca torres cerca de curvas"),
                ObjetivoTutorial("Diversifica tipos de torres"),
                ObjetivoTutorial("Ten al menos 3 torres")
            ])
            # Resaltar curvas importantes
            curvas = [(200, 400), (400, 200), (600, 600), (800, 300)]
            for curva in curvas:
                self.elementos_visuales.append(
                    ElementoTutorial("circulo", curva, "Punto estratégico", AZUL, 40)
                )
                
        elif self.fase_actual == FaseTutorial.OLEADAS:
            self.mensaje_principal = "¡Oleada de Enemigos!"
            self.mensaje_secundario = "Defiende tu base de múltiples enemigos"
            self.objetivos_actuales.append(ObjetivoTutorial("Sobrevive a la oleada"))
            self._iniciar_oleada_tutorial()
            
        elif self.fase_actual == FaseTutorial.VICTORIA:
            self.mensaje_principal = "¡Tutorial Completado!"
            self.mensaje_secundario = "Ya estás listo para el juego completo"
            self.objetivos_actuales.append(ObjetivoTutorial("Presiona ESC para volver al menú"))

    def _generar_enemigo_tutorial(self, tipo: str):
        """Genera un enemigo específico para el tutorial"""
        try:
            enemigo = crear_enemigo(tipo, self.juego.camino[0][0], self.juego.camino[0][1])
            enemigo.ruta = self.juego.camino
            self.juego.enemigos.append(enemigo)
            self.enemigos_tutorial_spawneados += 1
        except Exception as e:
            print(f"Error generando enemigo tutorial: {e}")

    def _generar_enemigos_variados(self):
        """Genera diferentes tipos de enemigos para mostrar variedad"""
        tipos = ['basico', 'rapido', 'tanque']
        for i, tipo in enumerate(tipos):
            try:
                x = self.juego.camino[0][0] - (i * 60)  # Espaciarlos
                enemigo = crear_enemigo(tipo, x, self.juego.camino[0][1])
                enemigo.ruta = self.juego.camino
                self.juego.enemigos.append(enemigo)
            except Exception as e:
                print(f"Error generando enemigo {tipo}: {e}")

    def _iniciar_oleada_tutorial(self):
        """Inicia una pequeña oleada para el tutorial"""
        import threading
        import time
        
        def generar_oleada():
            tipos = ['basico', 'basico', 'rapido', 'tanque', 'basico']
            for i, tipo in enumerate(tipos):
                time.sleep(2)  # Esperar 2 segundos entre enemigos
                if self.activo and self.fase_actual == FaseTutorial.OLEADAS:
                    try:
                        enemigo = crear_enemigo(tipo, self.juego.camino[0][0], self.juego.camino[0][1])
                        enemigo.ruta = self.juego.camino
                        self.juego.enemigos.append(enemigo)
                    except Exception as e:
                        print(f"Error en oleada tutorial: {e}")
        
        hilo_oleada = threading.Thread(target=generar_oleada)
        hilo_oleada.daemon = True
        hilo_oleada.start()

    def actualizar(self, dt: float):
        """Actualiza la lógica del tutorial"""
        if not self.activo:
            return
        
        self.tiempo_fase += dt
        
        # Actualizar elementos visuales
        for elemento in self.elementos_visuales[:]:
            elemento.actualizar(dt)
            if not elemento.activo:
                self.elementos_visuales.remove(elemento)
        
        # Verificar objetivos completados
        self._verificar_objetivos()
        
        # Lógica específica por fase
        self._actualizar_fase_especifica(dt)

    def _verificar_objetivos(self):
        """Verifica si los objetivos de la fase actual se han completado"""
        if self.fase_actual == FaseTutorial.INTERFAZ_BASICA:
            if self.tiempo_fase > 5000:  # 5 segundos
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.COLOCAR_TORRE:
            if len(self.juego.torres) > self.torres_colocadas:
                self.torres_colocadas = len(self.juego.torres)
                self.objetivos_actuales[0].completar()
                
        elif self.fase_actual == FaseTutorial.TIPOS_TORRES:
            # Verificar qué tipos de torres se han colocado
            for torre in self.juego.torres:
                tipo_torre = torre.__class__.__name__.lower()
                if 'cañon' in tipo_torre or 'cannon' in tipo_torre:
                    self.tipos_torres_probados.add('cañon')
                elif 'misil' in tipo_torre or 'missile' in tipo_torre:
                    self.tipos_torres_probados.add('misil')
                elif 'laser' in tipo_torre:
                    self.tipos_torres_probados.add('laser')
            
            # Completar objetivos basado en torres probadas
            if 'cañon' in self.tipos_torres_probados:
                self.objetivos_actuales[0].completar()
            if 'misil' in self.tipos_torres_probados:
                self.objetivos_actuales[1].completar()
            if 'laser' in self.tipos_torres_probados:
                self.objetivos_actuales[2].completar()
                
        elif self.fase_actual == FaseTutorial.PRIMER_ENEMIGO:
            # Contar enemigos eliminados
            enemigos_activos = sum(1 for e in self.juego.enemigos if e.activo)
            if self.enemigos_tutorial_spawneados > 0 and enemigos_activos == 0:
                self.objetivos_actuales[0].completar()
                
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            if len(self.juego.torres) >= 3:
                self.objetivos_actuales[2].completar()
            
        elif self.fase_actual == FaseTutorial.OLEADAS:
            # Verificar si sobrevivió a la oleada
            if self.tiempo_fase > 15000 and len(self.juego.enemigos) == 0:
                self.objetivos_actuales[0].completar()

    def _actualizar_fase_especifica(self, dt: float):
        """Actualiza lógica específica de cada fase"""
        if self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            # Actualizar dinero mostrado
            dinero_actual = self.juego.gestor_recursos.obtener('dinero')
            self.objetivos_actuales[0].descripcion = f"Dinero actual: ${dinero_actual}"
            
            if dinero_actual > 300:  # Ganó dinero
                self.objetivos_actuales[1].completar()
                self.objetivos_actuales[2].completar()

        # Verificar si todos los objetivos están completados
        if all(obj.completado for obj in self.objetivos_actuales):
            self.puede_continuar = True

    def manejar_evento(self, evento) -> bool:
        """Maneja eventos específicos del tutorial"""
        if not self.activo:
            return False
        
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_SPACE:
                if self.puede_continuar or self.fase_actual == FaseTutorial.INICIO:
                    self._avanzar_fase()
                    return True
                    
            elif evento.key == pygame.K_ESCAPE:
                self._salir_tutorial()
                return True
                
            elif evento.key == pygame.K_h:
                # Toggle ayuda
                return True
        
        return False

    def _avanzar_fase(self):
        """Avanza a la siguiente fase del tutorial"""
        fases = list(FaseTutorial)
        indice_actual = fases.index(self.fase_actual)
        
        if indice_actual < len(fases) - 1:
            self.fase_actual = fases[indice_actual + 1]
            self._cargar_fase()
        else:
            self._salir_tutorial()

    def _salir_tutorial(self):
        """Sale del tutorial y vuelve al menú"""
        self.activo = False
        # Aquí podrías cambiar el estado del juego de vuelta al menú
        from Main import EstadoJuego
        self.juego.estado_juego = EstadoJuego.MENU

    def dibujar(self, pantalla: pygame.Surface):
        """Dibuja todos los elementos del tutorial"""
        if not self.activo:
            return
        
        # Dibujar overlay semi-transparente
        overlay = pygame.Surface((1300, 800))
        overlay.set_alpha(100)
        overlay.fill(NEGRO)
        pantalla.blit(overlay, (0, 0))
        
        # Dibujar panel principal del tutorial
        self._dibujar_panel_principal(pantalla)
        
        # Dibujar objetivos
        self._dibujar_objetivos(pantalla)
        
        # Dibujar elementos visuales
        for elemento in self.elementos_visuales:
            elemento.dibujar(pantalla, self.fuente_pequeña)
        
        # Dibujar controles
        self._dibujar_controles(pantalla)

    def _dibujar_panel_principal(self, pantalla: pygame.Surface):
        """Dibuja el panel principal con el mensaje del tutorial"""
        panel_rect = pygame.Rect(50, 50, 500, 150)
        pygame.draw.rect(pantalla, BLANCO, panel_rect)
        pygame.draw.rect(pantalla, AZUL, panel_rect, 3)
        
        # Título
        titulo_surface = self.fuente_titulo.render(self.mensaje_principal, True, AZUL)
        titulo_rect = titulo_surface.get_rect(center=(panel_rect.centerx, panel_rect.y + 30))
        pantalla.blit(titulo_surface, titulo_rect)
        
        # Mensaje secundario
        if self.mensaje_secundario:
            mensaje_lines = self._dividir_texto(self.mensaje_secundario, 45)
            y_offset = 70
            for linea in mensaje_lines:
                texto_surface = self.fuente_texto.render(linea, True, NEGRO)
                texto_rect = texto_surface.get_rect(center=(panel_rect.centerx, panel_rect.y + y_offset))
                pantalla.blit(texto_surface, texto_rect)
                y_offset += 25

    def _dibujar_objetivos(self, pantalla: pygame.Surface):
        """Dibuja la lista de objetivos"""
        objetivos_rect = pygame.Rect(50, 220, 500, len(self.objetivos_actuales) * 30 + 40)
        pygame.draw.rect(pantalla, BLANCO, objetivos_rect)
        pygame.draw.rect(pantalla, VERDE, objetivos_rect, 3)
        
        # Título de objetivos
        titulo_obj = self.fuente_texto.render("Objetivos:", True, VERDE)
        pantalla.blit(titulo_obj, (objetivos_rect.x + 10, objetivos_rect.y + 10))
        
        # Lista de objetivos
        y_offset = 40
        for objetivo in self.objetivos_actuales:
            color = VERDE if objetivo.completado else NEGRO
            simbolo = "✓" if objetivo.completado else "○"
            
            texto = f"{simbolo} {objetivo.descripcion}"
            obj_surface = self.fuente_pequeña.render(texto, True, color)
            pantalla.blit(obj_surface, (objetivos_rect.x + 20, objetivos_rect.y + y_offset))
            y_offset += 30

    def _dibujar_controles(self, pantalla: pygame.Surface):
        """Dibuja los controles disponibles"""
        controles_rect = pygame.Rect(50, 720, 400, 70)
        pygame.draw.rect(pantalla, BLANCO, controles_rect)
        pygame.draw.rect(pantalla, MORADO, controles_rect, 3)
        
        controles = [
            "ESPACIO: Continuar (cuando esté disponible)",
            "H: Toggle ayuda", 
            "ESC: Salir del tutorial"
        ]
        
        y_offset = 10
        for control in controles:
            control_surface = self.fuente_pequeña.render(control, True, NEGRO)
            pantalla.blit(control_surface, (controles_rect.x + 10, controles_rect.y + y_offset))
            y_offset += 20

    def _dividir_texto(self, texto: str, max_chars: int) -> List[str]:
        """Divide texto en líneas que no excedan el máximo de caracteres"""
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