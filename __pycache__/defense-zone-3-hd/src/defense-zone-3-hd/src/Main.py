import pygame
import math
import random
import asyncio
import threading
from enum import Enum
from typing import List, Dict, Optional

# --- Módulos propios ---
from Enemigo import Enemigo, EnemigoBasico, EnemigoRapido, EnemigoTanque
from torres import torres
from misiles import misiles
from Excepcion_juego import (
    Excepcion_juego,
    ExcepcionRecursosInsuficientes,
    ExcepcionColocacionTorre,
)

pygame.init()

ANCHO_VENTANA = 1200
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

# =========================================================
#  🔧 Gestor de recursos
# =========================================================
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

# =========================================================
#  TORRES
# =========================================================
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
        lista_proyectiles.append(proyectil)
        self.ultimo_disparo = pygame.time.get_ticks()

class TorreCañon(TorreBase):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.costo = 50
        self.rango = 100
        self.daño = 25
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
        self.daño = 20
        self.intervalo_disparo = 800

# =========================================================
#  GENERADOR DE OLEADAS
# =========================================================
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

# =========================================================
#  JUEGO
# =========================================================
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
        self.fuente = pygame.font.Font(None, 36)
        self.fuente_pequeña = pygame.font.Font(None, 24)
        self.tareas_async = []
        self.gestor_recursos = GestorRecursos(dinero=200, vidas=20)

    def manejar_eventos(self):
        for evento in pygame.event.get():
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
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self.manejar_click(mouse_x, mouse_y)

    def manejar_click(self, x: int, y: int):
        if self.estado_juego == EstadoJuego.MENU:
            self.manejar_click_menu(x, y)
        elif self.estado_juego == EstadoJuego.JUGANDO:
            self.manejar_click_juego(x, y)

    def manejar_click_menu(self, x: int, y: int):
        if 450 <= x <= 750 and 300 <= y <= 350:
            self.iniciar_juego()
        elif 450 <= x <= 750 and 400 <= y <= 450:
            self.estado_juego = EstadoJuego.TUTORIAL
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
        self.oleada_actual = next(self.generador_oleadas)
        self.ultimo_tiempo_oleada = pygame.time.get_ticks()

    def cambiar_dificultad(self):
        if self.dificultad == NivelDificultad.FACIL:
            self.dificultad = NivelDificultad.MEDIO
        elif self.dificultad == NivelDificultad.MEDIO:
            self.dificultad = NivelDificultad.DIFICIL
        else:
            self.dificultad = NivelDificultad.FACIL

    def posicion_valida_torre(self, x: int, y: int) -> bool:
        # Implementar lógica para verificar si la posición es válida
        return True

    def colocar_torre(self, x: int, y: int, tipo: str):
        if tipo == 'cañon':
            torre = TorreCañon(x, y)
        elif tipo == 'misil':
            torre = TorreMisil(x, y)
        elif tipo == 'laser':
            torre = TorreLaser(x, y)
        else:
            raise ValueError("Tipo de torre desconocido")
        
        if self.gestor_recursos.gastar('dinero', torre.costo):
            self.torres.append(torre)
        else:
            raise ExcepcionRecursosInsuficientes("No hay suficiente dinero para colocar la torre")

    def actualizar(self):
        # Implementar lógica de actualización del juego
        pass

    def dibujar(self):
        self.pantalla.fill(BLANCO)
        # Implementar lógica de dibujo
        pygame.display.flip()

    def ejecutar(self):
        while self.ejecutando:
            self.manejar_eventos()
            if self.estado_juego == EstadoJuego.JUGANDO:
                self.actualizar()
            self.dibujar()
            self.reloj.tick(FPS)

if __name__ == "__main__":
    juego = DefenseZone3HD()
    juego.ejecutar()
    pygame.quit()