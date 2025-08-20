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

pygame.init()
pygame.mixer.init()


try:
    pygame.mixer.music.load("sonidos/Arcade_Game_Musica.mp3")
    pygame.mixer.music.play(-1)
except pygame.error:
    print("No se pudo cargar la música de fondo")


info = pygame.display.Info()
ANCHO_PANTALLA = info.current_w
ALTO_PANTALLA = info.current_h


USAR_PANTALLA_COMPLETA = True  

if USAR_PANTALLA_COMPLETA:
    ANCHO_VENTANA = ANCHO_PANTALLA
    ALTO_VENTANA = ALTO_PANTALLA
else:
    
    ANCHO_VENTANA = min(1600, int(ANCHO_PANTALLA * 0.85))
    ALTO_VENTANA = min(900, int(ALTO_PANTALLA * 0.85))

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


VERDE_OSCURO = (0, 100, 0)
AZUL_OSCURO = (25, 25, 112)
GRIS_CLARO_TUTORIAL = (248, 248, 255)


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

class misiles:
    def __init__(self, x_inicio, y_inicio, x_objetivo, y_objetivo):
        self.x = float(x_inicio)
        self.y = float(y_inicio)
        self.x_objetivo = float(x_objetivo)
        self.y_objetivo = float(y_objetivo)
        self.velocidad = 300  
        self.activo = True
        self.daño = 25  
        self.radio_colision = 15  
        
        
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
            
        
        self.x += self.vel_x * dt / 1000.0
        self.y += self.vel_y * dt / 1000.0
        
        
        distancia_objetivo = math.sqrt((self.x - self.x_objetivo)**2 + (self.y - self.y_objetivo)**2)
        if distancia_objetivo < 10:
            self.activo = False
        
        
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
        self.tipo = None

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

    def disparar(self, objetivo: Enemigo, lista_proyectiles: List[misiles], sonidos_disparo: Dict[str, pygame.mixer.Sound]):
        proyectil = misiles(self.x, self.y, objetivo.x, objetivo.y)
        proyectil.daño = self.daño  
        lista_proyectiles.append(proyectil)
        self.ultimo_disparo = pygame.time.get_ticks()
        
        if self.tipo in sonidos_disparo:
            try:
                sonidos_disparo[self.tipo].play()
            except pygame.error:
                pass  

class TorreCañon(TorreBase):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.costo = 50
        self.rango = 100
        self.daño = 35
        self.intervalo_disparo = 1500
        self.tipo = 'cañon'

class TorreMisil(TorreBase):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.costo = 100
        self.rango = 120
        self.daño = 50
        self.intervalo_disparo = 2000
        self.tipo = 'misil'

class TorreLaser(TorreBase):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.costo = 75
        self.rango = 80
        self.daño = 65
        self.intervalo_disparo = 800
        self.tipo = 'laser'


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
        
        
        self.fuente_titulo = pygame.font.SysFont("arial", 24, bold=True)
        self.fuente_texto = pygame.font.SysFont("arial", 18)
        self.fuente_pequeña = pygame.font.SysFont("arial", 16, bold=True)
        
        self.objetivos_actuales: List[ObjetivoTutorial] = []
        self.mensaje_principal = ""
        self.mensaje_secundario = ""
        self.puede_continuar = False
        self.torres_colocadas = 0
        self.enemigos_tutorial_spawneados = 0

    def iniciar_tutorial(self):
        self.activo = True
        self.fase_actual = FaseTutorial.INICIO
        self.juego.gestor_recursos.recursos = {"dinero": 300, "vidas": 10}
        self.juego.torres.clear()
        self.juego.enemigos.clear()
        self.juego.proyectiles.clear()
        self.torres_colocadas = 0
        self.enemigos_tutorial_spawneados = 0
        self._cargar_fase()

    def _cargar_fase(self):
        self.objetivos_actuales.clear()
        self.puede_continuar = False
        
        
        if hasattr(self, 'tiempo_inicio_tipos_enemigos'):
            delattr(self, 'tiempo_inicio_tipos_enemigos')
        if hasattr(self, 'tiempo_inicio_estrategia'):
            delattr(self, 'tiempo_inicio_estrategia')
        if hasattr(self, 'tiempo_oleada_completada'):
            delattr(self, 'tiempo_oleada_completada')
        
        if self.fase_actual == FaseTutorial.INICIO:
            self.mensaje_principal = "¡Bienvenido!"
            self.mensaje_secundario = "Aprende a defender tu base"
            self.objetivos_actuales.append(ObjetivoTutorial("Presiona ESPACIO para continuar"))
            
        elif self.fase_actual == FaseTutorial.INTERFAZ_BASICA:
            self.mensaje_principal = "Interfaz"
            self.mensaje_secundario = "Elementos básicos"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Dinero (arriba izquierda)"),
                ObjetivoTutorial("Vidas (arriba izquierda)"),
                ObjetivoTutorial("Torres: 1, 2, 3")
            ])
            
        elif self.fase_actual == FaseTutorial.COLOCAR_TORRE:
            self.mensaje_principal = "Primera Torre"
            self.mensaje_secundario = "Presiona '1' y haz clic"
            self.objetivos_actuales.append(ObjetivoTutorial("Coloca Torre Cañón ($50)"))
            
        elif self.fase_actual == FaseTutorial.TIPOS_TORRES:
            self.mensaje_principal = "Tipos de Torres"
            self.mensaje_secundario = "Experimenta diferentes tipos"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Torre Cañón (1) - $50"),
                ObjetivoTutorial("Torre Misil (2) - $100"), 
                ObjetivoTutorial("Torre Láser (3) - $75")
            ])
            
        elif self.fase_actual == FaseTutorial.PRIMER_ENEMIGO:
            self.mensaje_principal = "¡Primer Enemigo!"
            self.mensaje_secundario = "Torres atacan automáticamente"
            self.objetivos_actuales.append(ObjetivoTutorial("Elimina al enemigo rojo"))
            self._generar_enemigo_tutorial('basico')
            
        elif self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            self.mensaje_principal = "Recursos"
            self.mensaje_secundario = "Ganas dinero eliminando enemigos"
            dinero_actual = self.juego.gestor_recursos.obtener('dinero')
            self.objetivos_actuales.extend([
                ObjetivoTutorial(f"Dinero: ${dinero_actual}"),
                ObjetivoTutorial("Elimina enemigos → más dinero"),
                ObjetivoTutorial("Usa dinero sabiamente")
            ])
            self._generar_enemigos_recursos()
            
        elif self.fase_actual == FaseTutorial.TIPOS_ENEMIGOS:
            self.mensaje_principal = "Tipos de Enemigos"
            self.mensaje_secundario = "Observa las diferencias"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Rojo: Básico (50 HP)"),
                ObjetivoTutorial("Amarillo: Rápido (30 HP)"),
                ObjetivoTutorial("Gris: Tanque (120 HP)")
            ])
            self._generar_enemigos_variados()
            
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            self.mensaje_principal = "Estrategia"
            self.mensaje_secundario = "Torres en puntos estratégicos"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Torres en curvas"),
                ObjetivoTutorial("Diversifica tipos"),
                ObjetivoTutorial("Mín. 3 torres")
            ])
            
        elif self.fase_actual == FaseTutorial.OLEADAS:
            self.mensaje_principal = "¡Oleada!"
            self.mensaje_secundario = "Múltiples enemigos"
            self.objetivos_actuales.append(ObjetivoTutorial("Sobrevive a la oleada"))
            self._iniciar_oleada_tutorial()
            
        elif self.fase_actual == FaseTutorial.VICTORIA:
            self.mensaje_principal = "¡Completado!"
            self.mensaje_secundario = "Listo para el juego real"
            self.objetivos_actuales.append(ObjetivoTutorial("ESC para volver al menú"))

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

    def _generar_enemigos_recursos(self):
        
        for i in range(2):
            enemigo = EnemigoBasico(self.juego.camino[0][0], self.juego.camino[0][1])
            enemigo.ruta = self.juego.camino
            self.juego.enemigos.append(enemigo)

    def _generar_enemigos_variados(self):
        tipos = ['basico', 'rapido', 'tanque']
        for i, tipo in enumerate(tipos):
            clases_enemigos = {
                'basico': EnemigoBasico,
                'rapido': EnemigoRapido,
                'tanque': EnemigoTanque
            }
            if tipo in clases_enemigos:
                x = self.juego.camino[0][0] - (i * 60)
                enemigo = clases_enemigos[tipo](x, self.juego.camino[0][1])
                enemigo.ruta = self.juego.camino
                self.juego.enemigos.append(enemigo)

    def _iniciar_oleada_tutorial(self):
        import threading
        import time
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

    def _verificar_objetivos(self):
        if self.fase_actual == FaseTutorial.INTERFAZ_BASICA:
            for objetivo in self.objetivos_actuales:
                objetivo.completar()
                
        elif self.fase_actual == FaseTutorial.COLOCAR_TORRE:
            if len(self.juego.torres) > self.torres_colocadas:
                self.torres_colocadas = len(self.juego.torres)
                self.objetivos_actuales[0].completar()
        
        elif self.fase_actual == FaseTutorial.TIPOS_TORRES:
            
            tipos_colocados = set()
            for torre in self.juego.torres:
                if isinstance(torre, TorreCañon):
                    tipos_colocados.add('cañon')
                elif isinstance(torre, TorreMisil):
                    tipos_colocados.add('misil')
                elif isinstance(torre, TorreLaser):
                    tipos_colocados.add('laser')
            
            
            for objetivo in self.objetivos_actuales:
                if "Cañón" in objetivo.descripcion and 'cañon' in tipos_colocados:
                    objetivo.completar()
                elif "Misil" in objetivo.descripcion and 'misil' in tipos_colocados:
                    objetivo.completar()
                elif "Láser" in objetivo.descripcion and 'laser' in tipos_colocados:
                    objetivo.completar()
        
        elif self.fase_actual == FaseTutorial.PRIMER_ENEMIGO:
            enemigos_activos = sum(1 for e in self.juego.enemigos if e.activo)
            if self.enemigos_tutorial_spawneados > 0 and enemigos_activos == 0:
                self.objetivos_actuales[0].completar()
        
        elif self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            enemigos_activos = sum(1 for e in self.juego.enemigos if e.activo)
            
            for i, objetivo in enumerate(self.objetivos_actuales):
                if i == 0:  
                    objetivo.completar()
                elif "Elimina enemigos" in objetivo.descripcion and enemigos_activos == 0:
                    objetivo.completar()
                elif "Usa dinero" in objetivo.descripcion:
                    
                    if enemigos_activos == 0:
                        objetivo.completar()
        
        elif self.fase_actual == FaseTutorial.TIPOS_ENEMIGOS:
            
            
            
            enemigos_activos = sum(1 for e in self.juego.enemigos if e.activo)
            
            
            if enemigos_activos == 0:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
            else:
                
                tipos_enemigos_vistos = set()
                for enemigo in self.juego.enemigos:
                    if hasattr(enemigo, '__class__'):
                        if 'Basico' in enemigo.__class__.__name__:
                            tipos_enemigos_vistos.add('basico')
                        elif 'Rapido' in enemigo.__class__.__name__:
                            tipos_enemigos_vistos.add('rapido')
                        elif 'Tanque' in enemigo.__class__.__name__:
                            tipos_enemigos_vistos.add('tanque')
                
                
                for objetivo in self.objetivos_actuales:
                    if "Básico" in objetivo.descripcion and 'basico' in tipos_enemigos_vistos:
                        objetivo.completar()
                    elif "Rápido" in objetivo.descripcion and 'rapido' in tipos_enemigos_vistos:
                        objetivo.completar()
                    elif "Tanque" in objetivo.descripcion and 'tanque' in tipos_enemigos_vistos:
                        objetivo.completar()
        
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            
            for i, objetivo in enumerate(self.objetivos_actuales):
                if i == 0 and len(self.juego.torres) > 0:  
                    objetivo.completar()
                elif i == 1 and len(self.juego.torres) >= 2:  
                    
                    tipos_torres = set()
                    for torre in self.juego.torres:
                        if isinstance(torre, TorreCañon):
                            tipos_torres.add('cañon')
                        elif isinstance(torre, TorreMisil):
                            tipos_torres.add('misil')
                        elif isinstance(torre, TorreLaser):
                            tipos_torres.add('laser')
                    if len(tipos_torres) >= 2:
                        objetivo.completar()
                elif i == 2 and len(self.juego.torres) >= 3:  
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.OLEADAS:
            enemigos_activos = sum(1 for e in self.juego.enemigos if e.activo)
            if enemigos_activos == 0:
                
                import time
                if not hasattr(self, 'tiempo_oleada_completada'):
                    self.tiempo_oleada_completada = time.time()
                elif time.time() - self.tiempo_oleada_completada > 2: 
                    self.objetivos_actuales[0].completar()

        elif self.fase_actual == FaseTutorial.VICTORIA:
            
            pass

    def _logica_fase_especifica(self, dt: float):
        if self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            dinero_actual = self.juego.gestor_recursos.obtener('dinero')
            self.objetivos_actuales[0].descripcion = f"Dinero: ${dinero_actual}"
        
        elif self.fase_actual == FaseTutorial.TIPOS_ENEMIGOS:
            
            if not hasattr(self, 'tiempo_inicio_tipos_enemigos'):
                self.tiempo_inicio_tipos_enemigos = pygame.time.get_ticks()
            
            tiempo_transcurrido = pygame.time.get_ticks() - self.tiempo_inicio_tipos_enemigos
            
            
            if tiempo_transcurrido > 5000:  
                enemigos_activos = sum(1 for e in self.juego.enemigos if e.activo)
                if enemigos_activos == 0:
                    for objetivo in self.objetivos_actuales:
                        objetivo.completar()
        
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            
            if not hasattr(self, 'tiempo_inicio_estrategia'):
                self.tiempo_inicio_estrategia = pygame.time.get_ticks()
            
            tiempo_transcurrido = pygame.time.get_ticks() - self.tiempo_inicio_estrategia
            if tiempo_transcurrido > 10000 and len(self.juego.torres) >= 1:  
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
        
        
        self.puede_continuar = all(obj.completado for obj in self.objetivos_actuales)

    def actualizar(self, dt: float):
        if not self.activo:
            return
        self._verificar_objetivos()
        self._logica_fase_especifica(dt)

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
        """Interfaz minimalista que no tapa la ruta"""
        if not self.activo:
            return
        
        
        self._dibujar_panel_compacto(pantalla)
        
    
        self._dibujar_objetivos_minimalistas(pantalla)
        
        
        self._dibujar_progreso(pantalla)
        
        
        if self.puede_continuar:
            self._dibujar_indicador_continuar(pantalla)

    def _dibujar_panel_compacto(self, pantalla: pygame.Surface):
        """Panel compacto en esquina superior derecha"""
        panel_ancho = int(280 * ANCHO_VENTANA / 1300)
        panel_alto = int(70 * ALTO_VENTANA / 800)
        panel_x = ANCHO_VENTANA - panel_ancho - int(20 * ANCHO_VENTANA / 1300)
        panel_y = int(120 * ALTO_VENTANA / 800)  
        
        
        superficie = pygame.Surface((panel_ancho, panel_alto))
        superficie.set_alpha(220)
        superficie.fill(GRIS_CLARO_TUTORIAL)
        pantalla.blit(superficie, (panel_x, panel_y))
        
        
        pygame.draw.rect(pantalla, AZUL, (panel_x, panel_y, panel_ancho, panel_alto), 2)
        
        
        titulo = self.fuente_titulo.render(self.mensaje_principal, True, AZUL_OSCURO)
        pantalla.blit(titulo, (panel_x + 8, panel_y + 8))
        
        
        if self.mensaje_secundario:
            subtitulo = self.fuente_texto.render(self.mensaje_secundario, True, AZUL_OSCURO)
            pantalla.blit(subtitulo, (panel_x + 8, panel_y + 35))

    def _dibujar_objetivos_minimalistas(self, pantalla: pygame.Surface):
        """Objetivos en barra inferior compacta"""
        if not self.objetivos_actuales:
            return
        
        barra_alto = len(self.objetivos_actuales) * 22 + 30
        barra_ancho = int(380 * ANCHO_VENTANA / 1300)
        barra_x = int(20 * ANCHO_VENTANA / 1300)
        barra_y = ALTO_VENTANA - barra_alto - int(20 * ALTO_VENTANA / 800)
        
        
        superficie = pygame.Surface((barra_ancho, barra_alto))
        superficie.set_alpha(200)
        superficie.fill(GRIS_CLARO_TUTORIAL)
        pantalla.blit(superficie, (barra_x, barra_y))
        
        
        pygame.draw.rect(pantalla, VERDE_OSCURO, (barra_x, barra_y, barra_ancho, barra_alto), 2)
        
        
        titulo = self.fuente_pequeña.render("Objetivos:", True, VERDE_OSCURO)
        pantalla.blit(titulo, (barra_x + 8, barra_y + 6))
        
        
        y_offset = 25
        for i, objetivo in enumerate(self.objetivos_actuales):
            color = VERDE_OSCURO if objetivo.completado else AZUL_OSCURO
            simbolo = "✓" if objetivo.completado else f"{i+1}."
            texto = f"{simbolo} {objetivo.descripcion}"
            
            
            sombra = self.fuente_pequeña.render(texto, True, BLANCO)
            pantalla.blit(sombra, (barra_x + 11, barra_y + y_offset + 1))
            
            
            obj_surface = self.fuente_pequeña.render(texto, True, color)
            pantalla.blit(obj_surface, (barra_x + 10, barra_y + y_offset))
            y_offset += 22

    def _dibujar_progreso(self, pantalla: pygame.Surface):
        """Barra de progreso en la parte superior"""
        total_fases = len(FaseTutorial)
        fase_actual_num = list(FaseTutorial).index(self.fase_actual) + 1
        
        
        barra_ancho = 200
        barra_alto = 6
        barra_x = (ANCHO_VENTANA - barra_ancho) // 2
        barra_y = 12
        
        
        pygame.draw.rect(pantalla, GRIS_CLARO, (barra_x, barra_y, barra_ancho, barra_alto))
        
        
        progreso_ancho = int((fase_actual_num / total_fases) * barra_ancho)
        pygame.draw.rect(pantalla, VERDE_OSCURO, (barra_x, barra_y, progreso_ancho, barra_alto))
        
        
        texto_progreso = f"Tutorial: {fase_actual_num}/{total_fases}"
        superficie = self.fuente_pequeña.render(texto_progreso, True, AZUL_OSCURO)
        rect = superficie.get_rect(center=(ANCHO_VENTANA//2, barra_y + barra_alto + 12))
        pantalla.blit(superficie, rect)

    def _dibujar_indicador_continuar(self, pantalla: pygame.Surface):
        """Indicador para continuar en esquina inferior derecha"""
        if int(pygame.time.get_ticks() / 800) % 2:
            texto = "ESPACIO → continuar"
            superficie = self.fuente_pequeña.render(texto, True, VERDE_OSCURO)
            
            rect = superficie.get_rect()
            rect.x = ANCHO_VENTANA - rect.width - 25
            rect.y = ALTO_VENTANA - rect.height - 15
            
            
            fondo = rect.inflate(12, 6)
            fondo_surf = pygame.Surface(fondo.size)
            fondo_surf.set_alpha(180)
            fondo_surf.fill(GRIS_CLARO_TUTORIAL)
            pantalla.blit(fondo_surf, fondo.topleft)
            
            pygame.draw.rect(pantalla, VERDE_OSCURO, fondo, 2)
            pantalla.blit(superficie, rect)


class DefenseZone3HD:
    def __init__(self):
        
        if USAR_PANTALLA_COMPLETA:
            self.pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA), pygame.FULLSCREEN)
        else:
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
        
        
        escala_x = ANCHO_VENTANA / 1300
        escala_y = ALTO_VENTANA / 800
        
        self.camino = [
            (int(50 * escala_x), int(400 * escala_y)), 
            (int(200 * escala_x), int(400 * escala_y)), 
            (int(200 * escala_x), int(200 * escala_y)), 
            (int(400 * escala_x), int(200 * escala_y)),
            (int(400 * escala_x), int(600 * escala_y)), 
            (int(600 * escala_x), int(600 * escala_y)), 
            (int(600 * escala_x), int(300 * escala_y)), 
            (int(800 * escala_x), int(300 * escala_y)),
            (int(800 * escala_x), int(500 * escala_y)), 
            (int(1000 * escala_x), int(500 * escala_y)), 
            (int(1000 * escala_x), int(200 * escala_y)), 
            (int(1150 * escala_x), int(200 * escala_y))
        ]
        
        self.tipo_torre_seleccionada = 'cañon'
        
        
        tamaño_base = max(24, int(32 * min(escala_x, escala_y)))
        tamaño_pequeño = max(18, int(24 * min(escala_x, escala_y)))
        
        self.fuente = pygame.font.SysFont("arial", tamaño_base)
        self.fuente_pequeña = pygame.font.SysFont("arial", tamaño_pequeño)
        self.tareas_async = []
        self.gestor_recursos = GestorRecursos(dinero=200, vidas=20)
        self.interfaz = Interfaz(self.pantalla, self.fuente, self.fuente_pequeña)
        self.tutorial = TutorialInteractivo(self)
        
        
        self.sonidos_disparo = {}
        self._cargar_sonidos()

    def _cargar_sonidos(self):
        """Cargar todos los sonidos del juego"""
        try:
            self.sonidos_disparo = {
                'cañon': pygame.mixer.Sound("sonidos/Canon.mp3"),
                'misil': pygame.mixer.Sound("sonidos/Misil.mp3"),
                'laser': pygame.mixer.Sound("sonidos/Laser.mp3")
            }
        except pygame.error:
            print("No se pudieron cargar los sonidos de disparo")
            
            self.sonidos_disparo = {}

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

    def actualizar(self, dt: float):
        if self.estado_juego not in [EstadoJuego.JUGANDO, EstadoJuego.TUTORIAL]:
            return
        
        if self.estado_juego == EstadoJuego.TUTORIAL:
            self.tutorial.actualizar(dt)
        
        
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
                    else:
                        
                        self.gestor_recursos.ganar('dinero', 15)
                self.enemigos.remove(enemigo)
        
        
        tiempo_actual = pygame.time.get_ticks()
        for torre in self.torres:
            torre.objetivo = torre.encontrar_objetivo(self.enemigos)
            if torre.objetivo and torre.puede_disparar(tiempo_actual):
                torre.disparar(torre.objetivo, self.proyectiles, self.sonidos_disparo)
        
        
        for proyectil in self.proyectiles[:]:
            proyectil.actualizar(dt)
            
            
            if proyectil.activo:
                for enemigo in self.enemigos:
                    if proyectil.verificar_colision(enemigo):
                        
                        if hasattr(enemigo, 'recibir_daño'):
                            enemigo.recibir_daño(proyectil.daño)
                        elif hasattr(enemigo, 'hp'):
                            enemigo.hp -= proyectil.daño
                            if enemigo.hp <= 0:
                                enemigo.activo = False
                        
                        
                        proyectil.activo = False
                        break
            
            
            if not proyectil.activo:
                self.proyectiles.remove(proyectil)
        
        
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

    def dibujar_juego(self):
        
        if len(self.camino) > 1:
            pygame.draw.lines(self.pantalla, GRIS, False, self.camino, 5)
        
        
        for torre in self.torres:
            if hasattr(torre, 'dibujar'):
                torre.dibujar(self.pantalla)
            else:
                
                pygame.draw.circle(self.pantalla, AZUL, (torre.x, torre.y), 20)
                
                if hasattr(torre, 'rango'):
                    pygame.draw.circle(self.pantalla, (0, 0, 255, 50), (torre.x, torre.y), torre.rango, 1)
        
        
        for enemigo in self.enemigos:
            if hasattr(enemigo, 'dibujar'):
                enemigo.dibujar(self.pantalla)
            else:
                
                color_enemigo = ROJO
                if hasattr(enemigo, '__class__'):
                    if 'Rapido' in enemigo.__class__.__name__:
                        color_enemigo = AMARILLO
                    elif 'Tanque' in enemigo.__class__.__name__:
                        color_enemigo = GRIS_OSCURO
                
                pygame.draw.rect(self.pantalla, color_enemigo, (enemigo.x-10, enemigo.y-10, 20, 20))
            
            
            self.dibujar_barra_vida_enemigo(enemigo)
        
        
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
                
                
                pygame.draw.rect(self.pantalla, ROJO, 
                               (x_barra, y_barra, ancho_barra, alto_barra))
                
                
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