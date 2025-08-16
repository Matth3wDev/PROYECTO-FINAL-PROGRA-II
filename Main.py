import pygame
import math
import random
import asyncio
import threading
from enum import Enum
from typing import List, Dict, Optional


from Enemigo import Enemigo, EnemigoBasico, EnemigoRapido, EnemigoTanque
from torres import torres
from misiles import misiles
from Excepcion_juego import (
    ExcepcionRecursosInsuficientes,
    ExcepcionColocacionTorre,
)
from interfaz import Interfaz  
from Objetos import Objetos
from gestor_recursos import gestor_recursos

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
        self.interfaz = Interfaz(self.pantalla, self.fuente, self.fuente_pequeña)  # <--- Instancia de Interfaz

    def manejar_eventos(self):
        for evento in pygame.event.get():
            # --- Manejo de interfaz ---
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

    def iniciar_juego(self):
        self.estado_juego = EstadoJuego.JUGANDO
        self.generador_oleadas = GeneradorOleadas(self.dificultad)
        modificadores_dificultad = {
            NivelDificultad.FACIL: {'dinero': 300, 'vidas': 25},
            NivelDificultad.MEDIO: {'dinero': 200, 'vidas': 20},
            NivelDificultad.DIFICIL: {'dinero': 150, 'vidas': 15}
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

    def actualizar(self, dt: float):
        if self.estado_juego != EstadoJuego.JUGANDO:
            return

        for enemigo in self.enemigos[:]:
            enemigo.actualizar(dt)
            if not enemigo.activo:
                if hasattr(enemigo, 'indice_ruta') and enemigo.indice_ruta >= len(enemigo.ruta) - 1:
                    self.gestor_recursos.gastar('vidas', 1)
                    vidas_actuales = self.gestor_recursos.obtener('vidas')
                    if vidas_actuales <= 0:
                        self.estado_juego = EstadoJuego.GAME_OVER
                else:
                    if hasattr(enemigo, 'recompensa'):
                        self.gestor_recursos.ganar('dinero', enemigo.recompensa)
                self.enemigos.remove(enemigo)

        tiempo_actual = pygame.time.get_ticks()
        for torre in self.torres:
            torre.objetivo = torre.encontrar_objetivo(self.enemigos)
            if torre.objetivo and torre.puede_disparar(tiempo_actual):
                torre.disparar(torre.objetivo, self.proyectiles)

        for proyectil in self.proyectiles[:]:
            proyectil.actualizar(dt)
            if not proyectil.activo:
                self.proyectiles.remove(proyectil)

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
            self.dibujar_tutorial()
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

    def dibujar_tutorial(self):
        texto_tutorial = [
            "TUT0RIAL - Defense Zone 3 HD",
            "",
            "Objetivo: Defiende tu base de las oleadas de enemigos",
            "",
            "Controles:",
            "- Click izquierdo: Colocar torre",
            "- Tecla 1: Seleccionar Torre Cañón (50 monedas)",
            "- Tecla 2: Seleccionar Torre Misil (100 monedas)",
            "- Tecla 3: Seleccionar Torre Láser (75 monedas)",
            "- ESC: Pausar juego / Volver al menú",
            "",
            "Tipos de enemigos:",
            "- Rojos: Enemigos básicos (100 HP, velocidad normal)",
            "- Amarillos: Enemigos rápidos (60 HP, velocidad alta)",
            "- Grises: Enemigos tanque (300 HP, velocidad baja)",
            "",
            "Niveles de Dificultad:",
            "- Fácil: Más dinero y vidas",
            "- Medio: Balanceado",
            "- Difícil: Menos recursos, enemigos más fuertes",
            "",
            "¡Presiona ESC para volver al menú!"
        ]
        y_offset = 50
        for linea in texto_tutorial:
            if linea:
                color = NEGRO if not linea.startswith("-") else GRIS_OSCURO
                texto = self.fuente_pequeña.render(linea, True, color)
                self.pantalla.blit(texto, (50, y_offset))
            y_offset += 30

    def dibujar_juego(self):
        if len(self.camino) > 1:
            pygame.draw.lines(self.pantalla, GRIS, False, self.camino, 5)
        for torre in self.torres:
            if hasattr(torre, 'dibujar'):
                torre.dibujar(self.pantalla)
        for enemigo in self.enemigos:
            if hasattr(enemigo, 'dibujar'):
                enemigo.dibujar(self.pantalla)
        for proyectil in self.proyectiles:
            if hasattr(proyectil, 'dibujar'):
                proyectil.dibujar(self.pantalla)
        self.dibujar_ui()

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