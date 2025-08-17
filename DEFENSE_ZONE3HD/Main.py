from time import time
import pygame
import math
import random
import asyncio
import threading
from enum import Enum
from typing import List, Dict, Optional

from Enemigo import Enemigo, EnemigoBasico, EnemigoRapido, EnemigoTanque
from torres import torres
from Excepcion_juego import (
    ExcepcionRecursosInsuficientes,
    ExcepcionColocacionTorre,
)
from interfaz import Interfaz  
from Objetos import Objetos
from gestor_recursos import gestor_recursos
from tutorial import VERDE_CLARO, TutorialInteractivo 

pygame.init()

ANCHO_VENTANA = 1300
ALTO_VENTANA  = 800
FPS = 60

BLANCO = (255, 255, 255)
NEGRO  = (0, 0, 0)
ROJO   = (255, 0, 0)
VERDE  = (0, 255, 0)
AZUL   = (0, 0, 255)
AMARILLO = (255, 255, 0)
GRIS        = (128, 128, 128)
GRIS_OSCURO = (64, 64, 64)
GRIS_CLARO  = (192, 192, 192)

class EstadoJuego(Enum):
    MENU = 1
    TUTORIAL = 2
    JUGANDO = 3
    PAUSADO = 4
    GAME_OVER = 5

class NivelDificultad(Enum):
    FACIL = 1
    MEDIO = 2
    DIFICIL = 3

class GestorRecursos:
    def __init__(self, dinero: int = 0, vidas: int = 0):
        self.recursos = {"dinero": dinero, "vidas": vidas}

    def gastar(self, clave: str, valor: int) -> bool:
        actual = self.recursos.get(clave, 0)
        if actual >= valor:
            self.recursos[clave] = actual - valor
            return True
        return False

    def ganar(self, clave: str, valor: int) -> None:
        self.recursos[clave] = self.recursos.get(clave, 0) + valor

    def obtener(self, clave: str) -> int:
        return self.recursos.get(clave, 0)

# CLASE MISILES CORREGIDA CON SISTEMA DE COLISIONES
class misiles:
    def __init__(self, x_inicio, y_inicio, x_objetivo, y_objetivo):
        self.x = float(x_inicio)
        self.y = float(y_inicio)
        self.x_objetivo = float(x_objetivo)
        self.y_objetivo = float(y_objetivo)
        self.velocidad = 300  # píxeles por segundo
        self.activo = True
        self.daño = 25  # daño base
        self.radio_colision = 15  # radio para detectar colisiones
        
        # Calcular dirección
        dx = self.x_objetivo - self.x
        dy = self.y_objetivo - self.y
        distancia = math.sqrt(dx*dx + dy*dy)
        
        if distancia > 0:
            self.vel_x = (dx / distancia) * self.velocidad
            self.vel_y = (dy / distancia) * self.velocidad
        else:
            self.vel_x = self.vel_y = 0
    
    def actualizar(self, dt):
        if not self.activo:
            return
            
        # Mover proyectil
        self.x += self.vel_x * dt / 1000.0
        self.y += self.vel_y * dt / 1000.0
        
        # Verificar si llegó al objetivo (aproximadamente)
        distancia_objetivo = math.sqrt((self.x - self.x_objetivo)**2 + (self.y - self.y_objetivo)**2)
        if distancia_objetivo < 10:
            self.activo = False
        
        # Verificar límites de pantalla
        if self.x < 0 or self.x > ANCHO_VENTANA or self.y < 0 or self.y > ALTO_VENTANA:
            self.activo = False
    
    def verificar_colision(self, enemigo):
        """Verifica si el proyectil colisiona con un enemigo"""
        if not self.activo or not enemigo.activo:
            return False
            
        distancia = math.sqrt((self.x - enemigo.x)**2 + (self.y - enemigo.y)**2)
        return distancia <= self.radio_colision
    
    def dibujar(self, pantalla):
        if self.activo:
            pygame.draw.circle(pantalla, AMARILLO, (int(self.x), int(self.y)), 5)
            pygame.draw.circle(pantalla, NEGRO, (int(self.x), int(self.y)), 5, 2)

class TorreBase(torres):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.costo = 50
        self.ultimo_disparo = 0
        self.intervalo_disparo = 1000
        self.objetivo = None

    def puede_disparar(self, tiempo_actual: int) -> bool:
        return tiempo_actual - self.ultimo_disparo >= self.intervalo_disparo

    def encontrar_objetivo(self, enemigos: List[Enemigo]) -> Optional[Enemigo]:
        objetivo_mas_cercano = None
        distancia_minima = float('inf')
        for enemigo in enemigos:
            if getattr(enemigo, "activo", False):
                distancia = math.sqrt((self.x - enemigo.x)**2 + (self.y - enemigo.y)**2)
                if distancia <= self.rango and distancia < distancia_minima:
                    distancia_minima = distancia
                    objetivo_mas_cercano = enemigo
        return objetivo_mas_cercano

    def disparar(self, objetivo: Enemigo, lista_proyectiles: List[misiles]):
        proyectil = misiles(self.x, self.y, objetivo.x, objetivo.y)
        proyectil.daño = self.daño  # Asignar daño del proyectil
        lista_proyectiles.append(proyectil)
        self.ultimo_disparo = pygame.time.get_ticks()

class TorreCañon(TorreBase):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.costo = 50
        self.rango = 100
        self.daño = 35
        self.intervalo_disparo = 1500

class TorreMisil(TorreBase):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.costo = 100
        self.rango = 120
        self.daño = 50
        self.intervalo_disparo = 2000

class TorreLaser(TorreBase):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.costo = 75
        self.rango = 80
        self.daño = 65
        self.intervalo_disparo = 800

class GeneradorOleadas:
    def __init__(self, dificultad: NivelDificultad):
        self.dificultad = dificultad
        self.numero_oleada = 1
        self.configuraciones_oleadas = self._generar_configuraciones()

    def _generar_configuraciones(self) -> List[List[Dict]]:
        configuraciones = []
        multiplicador = {
            NivelDificultad.FACIL: 0.8,
            NivelDificultad.MEDIO: 1.0,
            NivelDificultad.DIFICIL: 1.3
        }[self.dificultad]
        for oleada in range(1, 11):
            config_oleada = []
            num_enemigos = min(oleada * 3, 15)
            for i in range(int(num_enemigos * multiplicador)):
                if oleada <= 3:
                    tipo = 'basico'
                elif oleada <= 6:
                    tipo = random.choice(['basico', 'rapido'])
                else:
                    tipo = random.choice(['basico', 'rapido', 'tanque'])
                config_oleada.append({
                    'tipo': tipo,
                    'retraso': i * 1.0
                })
            configuraciones.append(config_oleada)
        return configuraciones

    def __next__(self):
        if self.numero_oleada <= len(self.configuraciones_oleadas):
            config = self.configuraciones_oleadas[self.numero_oleada - 1]
            self.numero_oleada += 1
            return config
        else:
            raise StopIteration

# ----------- TUTORIAL INTERACTIVO (SOLO CAMBIOS CLAVE) -----------
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
        
        # Fuentes más pequeñas y elegantes
        self.fuente_titulo = pygame.font.SysFont("arial", 20, bold=True)
        self.fuente_texto = pygame.font.SysFont("arial", 16)
        self.fuente_pequeña = pygame.font.SysFont("arial", 14)
        
        self.objetivos_actuales: List[ObjetivoTutorial] = []
        self.mensaje_principal = ""
        self.mensaje_secundario = ""
        self.puede_continuar = False
        self.torres_colocadas = 0
        self.enemigos_tutorial_spawneados = 0
        self.tiempo_fase_inicio = 0

    def iniciar_tutorial(self):
        self.activo = True
        self.fase_actual = FaseTutorial.INICIO
        self.juego.gestor_recursos.recursos = {"dinero": 300, "vidas": 10}
        self.juego.torres.clear()
        self.juego.enemigos.clear()
        self.juego.proyectiles.clear()
        self.torres_colocadas = 0
        self.enemigos_tutorial_spawneados = 0
        self.tiempo_fase_inicio = pygame.time.get_ticks()
        self._cargar_fase()

    def _cargar_fase(self):
        self.objetivos_actuales.clear()
        self.puede_continuar = False
        self.tiempo_fase_inicio = pygame.time.get_ticks()
        
        if self.fase_actual == FaseTutorial.INICIO:
            self.mensaje_principal = "¡Bienvenido al Tutorial!"
            self.mensaje_secundario = "Aprenderás Defense Zone 3 HD paso a paso"
            self.objetivos_actuales.append(ObjetivoTutorial("Presiona ESPACIO para comenzar"))
            
        elif self.fase_actual == FaseTutorial.INTERFAZ_BASICA:
            self.mensaje_principal = "Interfaz del Juego"
            self.mensaje_secundario = "Observa los elementos de la pantalla"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Dinero (arriba izquierda): Para comprar torres"),
                ObjetivoTutorial("Vidas (arriba izquierda): Si llegan a 0, pierdes"),
                ObjetivoTutorial("Teclas 1,2,3: Seleccionar tipo de torre")
            ])
            
        elif self.fase_actual == FaseTutorial.COLOCAR_TORRE:
            self.mensaje_principal = "Colocar Primera Torre"
            self.mensaje_secundario = "Presiona '1' para Torre Cañón, luego haz clic"
            self.objetivos_actuales.append(ObjetivoTutorial("Coloca una Torre Cañón ($50)"))
            
        elif self.fase_actual == FaseTutorial.TIPOS_TORRES:
            self.mensaje_principal = "Tipos de Torres"
            self.mensaje_secundario = "Cada torre tiene características únicas"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Cañón (1): $50 - Equilibrada"),
                ObjetivoTutorial("Misil (2): $100 - Alto daño, lenta"), 
                ObjetivoTutorial("Láser (3): $75 - Rápida, menor daño")
            ])
            
        elif self.fase_actual == FaseTutorial.PRIMER_ENEMIGO:
            self.mensaje_principal = "¡Tu Primer Enemigo!"
            self.mensaje_secundario = "Las torres atacan automáticamente"
            self.objetivos_actuales.append(ObjetivoTutorial("Observa cómo tu torre dispara"))
            self._generar_enemigo_tutorial('basico')
            
        elif self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            self.mensaje_principal = "Recursos"
            self.mensaje_secundario = "Ganas dinero eliminando enemigos"
            dinero_actual = self.juego.gestor_recursos.obtener('dinero')
            self.objetivos_actuales.extend([
                ObjetivoTutorial(f"Dinero actual: ${dinero_actual}"),
                ObjetivoTutorial("Cada enemigo da dinero al morir"),
                ObjetivoTutorial("Usa el dinero para más torres")
            ])
            
        elif self.fase_actual == FaseTutorial.TIPOS_ENEMIGOS:
            self.mensaje_principal = "Tipos de Enemigos"
            self.mensaje_secundario = "Diferentes enemigos, diferentes estrategias"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Rojos: Básicos (50 HP, velocidad normal)"),
                ObjetivoTutorial("Amarillos: Rápidos (30 HP, muy veloces)"),
                ObjetivoTutorial("Grises: Tanques (120 HP, lentos pero duros)")
            ])
            self._generar_enemigos_variados()
            
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            self.mensaje_principal = "Estrategia"
            self.mensaje_secundario = "Coloca torres en puntos estratégicos"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Coloca torres cerca de curvas"),
                ObjetivoTutorial("Usa diferentes tipos"),
                ObjetivoTutorial("Ten al menos 3 torres activas")
            ])
            
        elif self.fase_actual == FaseTutorial.OLEADAS:
            self.mensaje_principal = "¡Oleada!"
            self.mensaje_secundario = "Defiende contra múltiples enemigos"
            self.objetivos_actuales.append(ObjetivoTutorial("Sobrevive a la oleada tutorial"))
            self._iniciar_oleada_tutorial()
            
        elif self.fase_actual == FaseTutorial.VICTORIA:
            self.mensaje_principal = "¡Completado!"
            self.mensaje_secundario = "Ya dominas lo básico"
            self.objetivos_actuales.append(ObjetivoTutorial("Presiona ESC para volver al menú"))

    def _generar_enemigo_tutorial(self, tipo: str):
        clases_enemigos = {
            'basico': EnemigoBasico,
            'rapido': EnemigoRapido,
            'tanque': EnemigoTanque
        }
        if tipo in clases_enemigos:
            enemigo = clases_enemigos[tipo](self.juego.camino[0][0], self.juego.camino[0][1])
            enemigo.ruta = self.juego.camino
            self.juego.enemigos.append(enemigo)
            self.enemigos_tutorial_spawneados += 1

    def _generar_enemigos_variados(self):
        tipos = ['basico', 'rapido', 'tanque']
        clases_enemigos = {
            'basico': EnemigoBasico,
            'rapido': EnemigoRapido,
            'tanque': EnemigoTanque
        }
        for i, tipo in enumerate(tipos):
            if tipo in clases_enemigos:
                x = self.juego.camino[0][0] - (i * 60)
                enemigo = clases_enemigos[tipo](x, self.juego.camino[0][1])
                enemigo.ruta = self.juego.camino
                self.juego.enemigos.append(enemigo)

    def _iniciar_oleada_tutorial(self):
        def generar_oleada():
            tipos = ['basico', 'basico', 'rapido', 'tanque', 'basico']
            clases_enemigos = {
                'basico': EnemigoBasico,
                'rapido': EnemigoRapido,
                'tanque': EnemigoTanque
            }
            for i, tipo in enumerate(tipos):
                time.sleep(1.5)
                if self.activo and self.fase_actual == FaseTutorial.OLEADAS:
                    if tipo in clases_enemigos:
                        enemigo = clases_enemigos[tipo](self.juego.camino[0][0], self.juego.camino[0][1])
                        enemigo.ruta = self.juego.camino
                        self.juego.enemigos.append(enemigo)
        
        hilo = threading.Thread(target=generar_oleada)
        hilo.daemon = True
        hilo.start()

    def actualizar(self, dt: float):
        if not self.activo:
            return
        
        self._verificar_objetivos()
        self._logica_fase_especifica(dt)

    def _verificar_objetivos(self):
        tiempo_transcurrido = pygame.time.get_ticks() - self.tiempo_fase_inicio
        
        if self.fase_actual == FaseTutorial.INTERFAZ_BASICA:
            # Auto-completar después de 3 segundos
            if tiempo_transcurrido > 3000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.COLOCAR_TORRE:
            if len(self.juego.torres) > self.torres_colocadas:
                self.torres_colocadas = len(self.juego.torres)
                self.objetivos_actuales[0].completar()
                
        elif self.fase_actual == FaseTutorial.TIPOS_TORRES:
            # Auto-completar después de 4 segundos
            if tiempo_transcurrido > 4000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.PRIMER_ENEMIGO:
            enemigos_activos = sum(1 for e in self.juego.enemigos if e.activo)
            if self.enemigos_tutorial_spawneados > 0 and enemigos_activos == 0:
                self.objetivos_actuales[0].completar()
                
        elif self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            # Auto-completar después de 3 segundos
            if tiempo_transcurrido > 3000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.TIPOS_ENEMIGOS:
            # Auto-completar después de 4 segundos
            if tiempo_transcurrido > 4000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            if len(self.juego.torres) >= 3:
                self.objetivos_actuales[2].completar()
            # Auto-completar otros después de tiempo
            if tiempo_transcurrido > 5000:
                self.objetivos_actuales[0].completar()
                self.objetivos_actuales[1].completar()
                
        elif self.fase_actual == FaseTutorial.OLEADAS:
            if len(self.juego.enemigos) == 0 and tiempo_transcurrido > 5000:
                self.objetivos_actuales[0].completar()

    def _logica_fase_especifica(self, dt: float):
        if self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            dinero_actual = self.juego.gestor_recursos.obtener('dinero')
            self.objetivos_actuales[0].descripcion = f"Dinero actual: ${dinero_actual}"
        
        # Verificar si puede continuar
        self.puede_continuar = all(obj.completado for obj in self.objetivos_actuales)

    def manejar_evento(self, evento) -> bool:
        if not self.activo:
            return False
            
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_SPACE:
                if self.puede_continuar or self.fase_actual == FaseTutorial.INICIO:
                    self._avanzar_fase()
                    return True
            elif evento.key == pygame.K_ESCAPE:
                if self.fase_actual == FaseTutorial.VICTORIA:
                    self._salir_tutorial()
                    return True
                    
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            # Permitir avanzar con clic también
            if self.puede_continuar:
                self._avanzar_fase()
                return True
                
        return False

    def _avanzar_fase(self):
        fases = list(FaseTutorial)
        indice_actual = fases.index(self.fase_actual)
        if indice_actual < len(fases) - 1:
            self.fase_actual = fases[indice_actual + 1]
            self._cargar_fase()
        else:
            self._salir_tutorial()

    def _salir_tutorial(self):
        self.activo = False
        self.juego.estado_juego = EstadoJuego.MENU

    def dibujar(self, pantalla: pygame.Surface):
        if not self.activo:
            return
        
        # Posiciones optimizadas para pantallas más pequeñas
        panel_x = 650
        panel_y = 50
        panel_ancho = 600
        panel_alto_principal = 100
        
        # Panel principal más compacto
        panel_principal = pygame.Rect(panel_x, panel_y, panel_ancho, panel_alto_principal)
        pygame.draw.rect(pantalla, BLANCO, panel_principal)
        pygame.draw.rect(pantalla, AZUL, panel_principal, 2)
        
        # Título
        titulo = self.fuente_titulo.render(self.mensaje_principal, True, AZUL)
        titulo_rect = titulo.get_rect(center=(panel_principal.centerx, panel_principal.y + 25))
        pantalla.blit(titulo, titulo_rect)
        
        # Mensaje secundario
        if self.mensaje_secundario:
            mensaje_lineas = self._dividir_texto(self.mensaje_secundario, 50)
            y_offset = 50
            for linea in mensaje_lineas:
                texto = self.fuente_texto.render(linea, True, NEGRO)
                texto_rect = texto.get_rect(center=(panel_principal.centerx, panel_principal.y + y_offset))
                pantalla.blit(texto, texto_rect)
                y_offset += 20
        
        # Panel de objetivos más compacto
        objetivos_y = panel_y + panel_alto_principal + 10
        altura_objetivos = min(len(self.objetivos_actuales) * 18 + 40, 120)
        panel_objetivos = pygame.Rect(panel_x, objetivos_y, panel_ancho, altura_objetivos)
        
        pygame.draw.rect(pantalla, GRIS_CLARO, panel_objetivos)
        pygame.draw.rect(pantalla, VERDE, panel_objetivos, 2)
        
        # Título objetivos
        titulo_obj = self.fuente_texto.render("Objetivos:", True, VERDE)
        pantalla.blit(titulo_obj, (panel_objetivos.x + 10, panel_objetivos.y + 8))
        
        # Lista de objetivos
        y_offset = 28
        for objetivo in self.objetivos_actuales:
            color = VERDE if objetivo.completado else NEGRO
            simbolo = "✓" if objetivo.completado else "•"
            texto = f"{simbolo} {objetivo.descripcion}"
            
            # Truncar texto si es muy largo
            if len(texto) > 65:
                texto = texto[:62] + "..."
            
            obj_surface = self.fuente_pequeña.render(texto, True, color)
            pantalla.blit(obj_surface, (panel_objetivos.x + 15, panel_objetivos.y + y_offset))
            y_offset += 18
        
        # Indicador de continuar
        if self.puede_continuar:
            continuar_y = objetivos_y + altura_objetivos + 10
            continuar_texto = "ESPACIO o CLIC para continuar"
            continuar_surface = self.fuente_pequeña.render(continuar_texto, True, VERDE)
            continuar_rect = continuar_surface.get_rect(center=(panel_x + panel_ancho//2, continuar_y))
            
            # Efecto parpadeante
            if int(pygame.time.get_ticks() / 600) % 2:
                pygame.draw.rect(pantalla, VERDE_CLARO, continuar_rect.inflate(10, 6))
                pygame.draw.rect(pantalla, VERDE, continuar_rect.inflate(10, 6), 2)
                pantalla.blit(continuar_surface, continuar_rect)

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

# ----------- JUEGO PRINCIPAL -----------
class DefenseZone3HD:
    def __init__(self):
        self.pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
        pygame.display.set_caption("Defense Zone 3 HD")
        self.reloj = pygame.time.Clock()
        self.ejecutando = True
        self.estado_juego = EstadoJuego.MENU
        self.dificultad = NivelDificultad.MEDIO
        self.torres: List[TorreBase] = []
        self.enemigos: List[Enemigo] = []
        self.proyectiles: List[misiles] = []
        self.generador_oleadas: Optional[GeneradorOleadas] = None
        self.oleada_actual = []
        self.temporizador_oleada = 0
        self.retraso_oleada = 10000
        self.ultimo_tiempo_oleada = 0
        self.camino = [
            (50, 400), (200, 400), (200, 200), (400, 200),
            (400, 600), (600, 600), (600, 300), (800, 300),
            (800, 500), (1000, 500), (1000, 200), (1150, 200)
        ]
        self.tipo_torre_seleccionada = 'cañon'
        self.fuente = pygame.font.SysFont("arial", 36)
        self.fuente_pequeña = pygame.font.SysFont("arial", 24)
        self.tareas_async = []
        self.gestor_recursos = GestorRecursos(dinero=200, vidas=20)
        self.interfaz = Interfaz(self.pantalla, self.fuente, self.fuente_pequeña)
        self.tutorial = TutorialInteractivo(self)

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if self.estado_juego == EstadoJuego.TUTORIAL:
                if self.tutorial.manejar_evento(evento):
                    continue
            if self.estado_juego == EstadoJuego.MENU:
                resultado = self.interfaz.manejar_evento(evento, "MENU")
                if resultado == "SALIR":
                    self.ejecutando = False
            elif self.estado_juego == EstadoJuego.JUGANDO:
                resultado = self.interfaz.manejar_evento(evento, "JUGANDO")
                if resultado == "MENU":
                    self.estado_juego = EstadoJuego.MENU
            if evento.type == pygame.QUIT:
                self.ejecutando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    if self.estado_juego == EstadoJuego.JUGANDO:
                        self.estado_juego = EstadoJuego.PAUSADO
                    elif self.estado_juego == EstadoJuego.PAUSADO:
                        self.estado_juego = EstadoJuego.JUGANDO
                    elif self.estado_juego in [EstadoJuego.TUTORIAL, EstadoJuego.GAME_OVER]:
                        self.estado_juego = EstadoJuego.MENU
                elif evento.key == pygame.K_1:
                    self.tipo_torre_seleccionada = 'cañon'
                elif evento.key == pygame.K_2:
                    self.tipo_torre_seleccionada = 'misil'
                elif evento.key == pygame.K_3:
                    self.tipo_torre_seleccionada = 'laser'
                elif evento.key == pygame.K_SPACE and self.estado_juego == EstadoJuego.MENU:
                    self.iniciar_juego()
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self.manejar_click(mouse_x, mouse_y)

    def manejar_click(self, x: int, y: int):
        if self.estado_juego == EstadoJuego.MENU:
            self.manejar_click_menu(x, y)
        elif self.estado_juego in [EstadoJuego.JUGANDO, EstadoJuego.TUTORIAL]:
            self.manejar_click_juego(x, y)

    def manejar_click_menu(self, x: int, y: int):
        if 450 <= x <= 750 and 300 <= y <= 350:
            self.iniciar_juego()
        elif 450 <= x <= 750 and 400 <= y <= 450:
            self.estado_juego = EstadoJuego.TUTORIAL
            self.tutorial.iniciar_tutorial()
        elif 450 <= x <= 750 and 500 <= y <= 550:
            self.cambiar_dificultad()

    def manejar_click_juego(self, x: int, y: int):
        try:
            if self.posicion_valida_torre(x, y):
                self.colocar_torre(x, y, self.tipo_torre_seleccionada)
            else:
                raise ExcepcionColocacionTorre("No se puede colocar torre en esta posición")
        except ExcepcionColocacionTorre as e:
            print(f"Error de colocación: {e}")
        except ExcepcionRecursosInsuficientes as e:
            print(f"Error de recursos: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")

    def iniciar_juego(self):
        self.estado_juego = EstadoJuego.JUGANDO
        self.generador_oleadas = GeneradorOleadas(self.dificultad)
        modificadores_dificultad = {
            NivelDificultad.FACIL: {'dinero': 300, 'vidas': 5},
            NivelDificultad.MEDIO: {'dinero': 200, 'vidas': 3},
            NivelDificultad.DIFICIL: {'dinero': 150, 'vidas': 1}
        }
        mods = modificadores_dificultad[self.dificultad]
        self.gestor_recursos.recursos.update(mods)
        self.torres.clear()
        self.enemigos.clear()
        self.proyectiles.clear()
        self.ultimo_tiempo_oleada = pygame.time.get_ticks()

    def cambiar_dificultad(self):
        dificultades = list(NivelDificultad)
        indice_actual = dificultades.index(self.dificultad)
        self.dificultad = dificultades[(indice_actual + 1) % len(dificultades)]

    def posicion_valida_torre(self, x: int, y: int) -> bool:
        for camino_x, camino_y in self.camino:
            distancia = math.sqrt((x - camino_x)**2 + (y - camino_y)**2)
            if distancia < 50:
                return False
        for torre in self.torres:
            distancia = math.sqrt((x - torre.x)**2 + (y - torre.y)**2)
            if distancia < 60:
                return False
        return True

    def colocar_torre(self, x: int, y: int, tipo_torre: str):
        clases_torres = {
            'cañon': TorreCañon,
            'misil': TorreMisil,
            'laser': TorreLaser
        }
        if tipo_torre not in clases_torres:
            return
        clase_torre = clases_torres[tipo_torre]
        torre_nueva = clase_torre(x, y)
        if not self.gestor_recursos.gastar('dinero', torre_nueva.costo):
            raise ExcepcionRecursosInsuficientes(
                f"No tienes suficiente dinero para {tipo_torre}"
            )
        self.torres.append(torre_nueva)

    async def generar_oleada_async(self):
        try:
            if self.generador_oleadas is None:
                return
            config_oleada = next(self.generador_oleadas)
            for config_enemigo in config_oleada:
                await asyncio.sleep(config_enemigo['retraso'])
                tipo_enemigo = config_enemigo['tipo']
                clases_enemigos = {
                    'basico': EnemigoBasico,
                    'rapido': EnemigoRapido,
                    'tanque': EnemigoTanque
                }
                if tipo_enemigo in clases_enemigos:
                    clase_enemigo = clases_enemigos[tipo_enemigo]
                    enemigo = clase_enemigo(self.camino[0][0], self.camino[0][1])
                    enemigo.ruta = self.camino
                    self.enemigos.append(enemigo)
        except StopIteration:
            print("Todas las oleadas completadas")
        except Exception as e:
            print(f"Error en generación de oleada: {e}")

    # MÉTODO ACTUALIZAR CORREGIDO CON SISTEMA DE COLISIONES
    def actualizar(self, dt: float):
        if self.estado_juego not in [EstadoJuego.JUGANDO, EstadoJuego.TUTORIAL]:
            return
        
        if self.estado_juego == EstadoJuego.TUTORIAL:
            self.tutorial.actualizar(dt)
        
        # Actualizar enemigos
        for enemigo in self.enemigos[:]:
            enemigo.actualizar(dt)
            if not enemigo.activo:
                if hasattr(enemigo, 'indice_ruta') and enemigo.indice_ruta >= len(enemigo.ruta) - 1:
                    # Enemigo llegó al final - quitar vida
                    self.gestor_recursos.gastar('vidas', 1)
                    vidas_actuales = self.gestor_recursos.obtener('vidas')
                    if vidas_actuales <= 0:
                        self.estado_juego = EstadoJuego.GAME_OVER
                else:
                    # Enemigo eliminado por daño - dar recompensa
                    if hasattr(enemigo, 'recompensa'):
                        self.gestor_recursos.ganar('dinero', enemigo.recompensa)
                    else:
                        # Recompensa por defecto si no tiene atributo
                        self.gestor_recursos.ganar('dinero', 15)
                self.enemigos.remove(enemigo)
        
        # Actualizar torres
        tiempo_actual = pygame.time.get_ticks()
        for torre in self.torres:
            torre.objetivo = torre.encontrar_objetivo(self.enemigos)
            if torre.objetivo and torre.puede_disparar(tiempo_actual):
                torre.disparar(torre.objetivo, self.proyectiles)
        
        # NUEVA LÓGICA: Actualizar proyectiles Y verificar colisiones
        for proyectil in self.proyectiles[:]:
            proyectil.actualizar(dt)
            
            # Verificar colisiones con enemigos
            if proyectil.activo:
                for enemigo in self.enemigos:
                    if proyectil.verificar_colision(enemigo):
                        # Aplicar daño al enemigo
                        if hasattr(enemigo, 'recibir_daño'):
                            enemigo.recibir_daño(proyectil.daño)
                        elif hasattr(enemigo, 'hp'):
                            enemigo.hp -= proyectil.daño
                            if enemigo.hp <= 0:
                                enemigo.activo = False
                        
                        # Desactivar proyectil después del impacto
                        proyectil.activo = False
                        break
            
            # Remover proyectiles inactivos
            if not proyectil.activo:
                self.proyectiles.remove(proyectil)
        
        # Solo generar oleadas si está jugando (no en tutorial)
        if self.estado_juego == EstadoJuego.JUGANDO:
            if len(self.enemigos) == 0 and tiempo_actual - self.ultimo_tiempo_oleada > self.retraso_oleada:
                self.ultimo_tiempo_oleada = tiempo_actual
                def hilo_oleada():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.generar_oleada_async())
                        loop.close()
                    except Exception as e:
                        print(f"Error en hilo de oleada: {e}")
                hilo = threading.Thread(target=hilo_oleada)
                hilo.daemon = True
                hilo.start()

    def dibujar(self):
        self.pantalla.fill(BLANCO)
        if self.estado_juego == EstadoJuego.MENU:
            self.dibujar_menu()
            self.interfaz.dibujar_menu()
        elif self.estado_juego == EstadoJuego.TUTORIAL:
            self.dibujar_juego()
            self.tutorial.dibujar(self.pantalla)
        elif self.estado_juego == EstadoJuego.JUGANDO:
            self.dibujar_juego()
            self.interfaz.dibujar_juego()
        elif self.estado_juego == EstadoJuego.PAUSADO:
            self.dibujar_juego()
            self.dibujar_pausa()
        elif self.estado_juego == EstadoJuego.GAME_OVER:
            self.dibujar_juego()
            self.dibujar_game_over()
        pygame.display.flip()

    def dibujar_menu(self):
        titulo = self.fuente.render("Defense Zone 3 HD", True, NEGRO)
        rect_titulo = titulo.get_rect(center=(ANCHO_VENTANA//2, 200))
        self.pantalla.blit(titulo, rect_titulo)
        botones = [
            ("Jugar", 300),
            ("Tutorial", 400),
            (f"Dificultad: {self.dificultad.name}", 500)
        ]
        for texto, y in botones:
            rect_boton = pygame.Rect(450, y, 300, 50)
            pygame.draw.rect(self.pantalla, GRIS_CLARO, rect_boton)
            pygame.draw.rect(self.pantalla, NEGRO, rect_boton, 2)
            texto_boton = self.fuente_pequeña.render(texto, True, NEGRO)
            rect_texto = texto_boton.get_rect(center=rect_boton.center)
            self.pantalla.blit(texto_boton, rect_texto)

    # MÉTODO DIBUJAR_JUEGO MEJORADO CON BARRAS DE VIDA
    def dibujar_juego(self):
        # Dibujar camino
        if len(self.camino) > 1:
            pygame.draw.lines(self.pantalla, GRIS, False, self.camino, 5)
        
        # Dibujar torres con rangos (opcional)
        for torre in self.torres:
            if hasattr(torre, 'dibujar'):
                torre.dibujar(self.pantalla)
            else:
                # Dibujo básico de torre
                pygame.draw.circle(self.pantalla, AZUL, (torre.x, torre.y), 20)
                # Mostrar rango si es la torre seleccionada (opcional)
                if hasattr(torre, 'rango'):
                    pygame.draw.circle(self.pantalla, (0, 0, 255, 50), (torre.x, torre.y), torre.rango, 1)
        
        # Dibujar enemigos con barras de vida
        for enemigo in self.enemigos:
            if hasattr(enemigo, 'dibujar'):
                enemigo.dibujar(self.pantalla)
            else:
                # Dibujo básico del enemigo
                color_enemigo = ROJO
                if hasattr(enemigo, '__class__'):
                    if 'Rapido' in enemigo.__class__.__name__:
                        color_enemigo = AMARILLO
                    elif 'Tanque' in enemigo.__class__.__name__:
                        color_enemigo = GRIS_OSCURO
                
                pygame.draw.rect(self.pantalla, color_enemigo, (enemigo.x-10, enemigo.y-10, 20, 20))
            
            # Dibujar barra de vida
            self.dibujar_barra_vida_enemigo(enemigo)
        
        # Dibujar proyectiles
        for proyectil in self.proyectiles:
            proyectil.dibujar(self.pantalla)
        
        self.dibujar_ui()

    def dibujar_barra_vida_enemigo(self, enemigo):
        """Dibuja una barra de vida sobre el enemigo"""
        if hasattr(enemigo, 'hp') and hasattr(enemigo, 'hp_max'):
            if enemigo.hp < enemigo.hp_max:
                ancho_barra = 30
                alto_barra = 4
                x_barra = enemigo.x - ancho_barra // 2
                y_barra = enemigo.y - 20
                
                # Fondo de la barra (rojo)
                pygame.draw.rect(self.pantalla, ROJO, 
                               (x_barra, y_barra, ancho_barra, alto_barra))
                
                # Vida actual (verde)
                porcentaje_vida = max(0, enemigo.hp / enemigo.hp_max)
                ancho_vida = int(ancho_barra * porcentaje_vida)
                pygame.draw.rect(self.pantalla, VERDE, 
                               (x_barra, y_barra, ancho_vida, alto_barra))

    def dibujar_ui(self):
        dinero = self.gestor_recursos.obtener('dinero')
        vidas = self.gestor_recursos.obtener('vidas')
        texto_dinero = self.fuente_pequeña.render(f"Dinero: ${dinero}", True, NEGRO)
        texto_vidas  = self.fuente_pequeña.render(f"Vidas: {vidas}", True, NEGRO)
        self.pantalla.blit(texto_dinero, (10, 10))
        self.pantalla.blit(texto_vidas, (10, 40))
        
        info_torres = [
            ("1 - Cañón: $50", 'cañon'),
            ("2 - Misil: $100", 'misil'),
            ("3 - Láser: $75", 'laser')
        ]
        y_offset = 10
        for texto, tipo_torre in info_torres:
            color = VERDE if tipo_torre == self.tipo_torre_seleccionada else NEGRO
            texto_torre = self.fuente_pequeña.render(texto, True, color)
            self.pantalla.blit(texto_torre, (ANCHO_VENTANA - 200, y_offset))
            y_offset += 25
        
        if self.generador_oleadas:
            texto_oleada = self.fuente_pequeña.render(f"Oleada: {self.generador_oleadas.numero_oleada}", True, NEGRO)
            self.pantalla.blit(texto_oleada, (10, 70))
        
        # Mostrar estadísticas adicionales
        texto_enemigos = self.fuente_pequeña.render(f"Enemigos: {len(self.enemigos)}", True, NEGRO)
        self.pantalla.blit(texto_enemigos, (10, 100))
        
        texto_torres = self.fuente_pequeña.render(f"Torres: {len(self.torres)}", True, NEGRO)
        self.pantalla.blit(texto_torres, (10, 130))

    def dibujar_pausa(self):
        overlay = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA))
        overlay.set_alpha(128)
        overlay.fill(NEGRO)
        self.pantalla.blit(overlay, (0, 0))
        texto_pausa = self.fuente.render("JUEGO PAUSADO", True, BLANCO)
        rect_pausa = texto_pausa.get_rect(center=(ANCHO_VENTANA//2, ALTO_VENTANA//2))
        self.pantalla.blit(texto_pausa, rect_pausa)
        texto_reanudar = self.fuente_pequeña.render("Presiona ESC para continuar", True, BLANCO)
        rect_reanudar = texto_reanudar.get_rect(center=(ANCHO_VENTANA//2, ALTO_VENTANA//2 + 50))
        self.pantalla.blit(texto_reanudar, rect_reanudar)

    def dibujar_game_over(self):
        overlay = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA))
        overlay.set_alpha(128)
        overlay.fill(ROJO)
        self.pantalla.blit(overlay, (0, 0))
        texto_game_over = self.fuente.render("GAME OVER", True, BLANCO)
        rect_game_over = texto_game_over.get_rect(center=(ANCHO_VENTANA//2, ALTO_VENTANA//2))
        self.pantalla.blit(texto_game_over, rect_game_over)
        if self.generador_oleadas:
            texto_oleada = self.fuente_pequeña.render(f"Llegaste a la oleada: {self.generador_oleadas.numero_oleada}", True, BLANCO)
            rect_oleada = texto_oleada.get_rect(center=(ANCHO_VENTANA//2, ALTO_VENTANA//2 + 40))
            self.pantalla.blit(texto_oleada, rect_oleada)
        texto_reiniciar = self.fuente_pequeña.render("Presiona ESC para volver al menú", True, BLANCO)
        rect_reiniciar = texto_reiniciar.get_rect(center=(ANCHO_VENTANA//2, ALTO_VENTANA//2 + 70))
        self.pantalla.blit(texto_reiniciar, rect_reiniciar)

    def ejecutar(self):
        while self.ejecutando:
            dt = self.reloj.tick(FPS)
            self.manejar_eventos()
            self.actualizar(dt)
            self.dibujar()
        pygame.quit()

if __name__ == "__main__":
    try:
        juego = DefenseZone3HD()
        juego.ejecutar()
    except Exception as e:
        print(f"Error crítico del juego: {e}") 