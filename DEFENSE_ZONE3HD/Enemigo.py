import pygame
import math
import random
from typing import List, Tuple, Optional, Callable
from Objetos import Objetos
from Excepcion_juego import ExcepcionGeneracionEnemigo

COLORES_ENEMIGOS = {
    'basico': (255, 0, 0),
    'rapido': (255, 255, 0),
    'tanque': (64, 64, 64),
}

class Enemigo(Objetos): 
    def __init__(self, x: float, y: float, vida: int, velocidad: float, 
                 recompensa: int, tipo_enemigo: str = "basico"):
        super().__init__(x, y)
        self._vida_maxima = max(1, int(vida))
        self._vida = self._vida_maxima
        self._velocidad = max(0.1, float(velocidad))
        self._recompensa = max(0, int(recompensa))
        self._ruta: List[Tuple[float, float]] = []
        self._indice_ruta = 0
        self._progreso_movimiento = 0.0
        self._tipo_enemigo = tipo_enemigo
        self._color = COLORES_ENEMIGOS.get(tipo_enemigo, COLORES_ENEMIGOS['basico'])
        self._tamaño = 15
        self._desplazamiento_animacion = random.uniform(0, 2 * math.pi)
        self._esta_ralentizado = False
        self._duracion_ralentizacion = 0.0
        self._modificador_daño = lambda daño: daño
        self._modificador_velocidad = lambda velocidad: velocidad
        # --- EFECTO VISUAL DE DAÑO ---
        self._recibio_daño = False
        self._tiempo_daño = 0

    @property
    def vida(self) -> int:
        return self._vida
    
    @property
    def vida_maxima(self) -> int:
        return self._vida_maxima
    
    @property
    def velocidad(self) -> float:
        return self._velocidad
    
    @property
    def recompensa(self) -> int:
        return self._recompensa
    
    @property
    def tipo_enemigo(self) -> str:
        return self._tipo_enemigo
    
    @property
    def ruta(self) -> List[Tuple[float, float]]:
        return self._ruta
    
    @ruta.setter
    def ruta(self, nueva_ruta: List[Tuple[float, float]]):
        if not nueva_ruta:
            raise ExcepcionGeneracionEnemigo(
                "El camino no puede estar vacío",
                tipo_enemigo=self._tipo_enemigo,
                posicion_generacion=(self.x, self.y)
            )
        self._ruta = nueva_ruta.copy()
        self._indice_ruta = 0
    
    @property
    def indice_ruta(self) -> int:
        return self._indice_ruta
    
    def recibir_daño(self, daño: int, tipo_daño: str = "normal") -> bool:
        daño_modificado = self._modificador_daño(daño)
        daño_final = self._calcular_resistencia_daño(daño_modificado, tipo_daño)
        self._vida -= daño_final
        # --- EFECTO VISUAL DE DAÑO ---
        self._recibio_daño = True
        self._tiempo_daño = 150  # milisegundos de parpadeo
        if self._vida <= 0:
            self._vida = 0
            self.activo = False
            return True
        return False
    
    def _calcular_resistencia_daño(self, daño: int, tipo_daño: str) -> int:
        return daño
    
    def curar(self, cantidad: int):
        self._vida = min(self._vida_maxima, self._vida + cantidad)
    
    def aplicar_ralentizacion(self, duracion: float, factor_ralentizacion: float = 0.5):
        self._esta_ralentizado = True
        self._duracion_ralentizacion = duracion
        self._modificador_velocidad = lambda velocidad: velocidad * factor_ralentizacion
    
    def obtener_velocidad_actual(self) -> float:
        velocidad_base = self._modificador_velocidad(self._velocidad)
        return velocidad_base
    
    def obtener_porcentaje_vida(self) -> float:
        return self._vida / self._vida_maxima if self._vida_maxima > 0 else 0.0
    
    def esta_al_final_de_la_ruta(self) -> bool:
        return self._indice_ruta >= len(self._ruta) - 1
    
    def actualizar(self, dt: float):
        # --- EFECTO VISUAL DE DAÑO ---
        if self._recibio_daño:
            self._tiempo_daño -= dt
            if self._tiempo_daño <= 0:
                self._recibio_daño = False
        if not self.activo or not self._ruta:
            return
        self._actualizar_efectos_estado(dt)
        self._mover_a_lo_largo_de_la_ruta(dt)
        if self.esta_al_final_de_la_ruta():
            distancia_al_final = self.distancia_a_punto(self._ruta[-1])
            if distancia_al_final < 10:
                self.activo = False
    
    def _actualizar_efectos_estado(self, dt: float):
        if self._esta_ralentizado:
            self._duracion_ralentizacion -= dt
            if self._duracion_ralentizacion <= 0:
                self._esta_ralentizado = False
                self._modificador_velocidad = lambda velocidad: velocidad
    
    def _mover_a_lo_largo_de_la_ruta(self, dt: float):
        if self._indice_ruta >= len(self._ruta) - 1:
            return
        posicion_actual = (self.x, self.y)
        posicion_objetivo = self._ruta[self._indice_ruta + 1]
        dx = posicion_objetivo[0] - posicion_actual[0]
        dy = posicion_objetivo[1] - posicion_actual[1]
        distancia = math.sqrt(dx * dx + dy * dy)
        if distancia < 5:
            self._indice_ruta += 1
            if self._indice_ruta < len(self._ruta):
                self.establecer_posicion(*self._ruta[self._indice_ruta])
        else:
            velocidad_actual = self.obtener_velocidad_actual()
            distancia_movimiento = velocidad_actual * dt / 1000.0
            if distancia > 0:
                mover_x = (dx / distancia) * distancia_movimiento
                mover_y = (dy / distancia) * distancia_movimiento
                self.establecer_posicion(self.x + mover_x, self.y + mover_y)
    
    def distancia_a_punto(self, punto: Tuple[float, float]) -> float:
        dx = self.x - punto[0]
        dy = self.y - punto[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def dibujar(self, pantalla: pygame.Surface):
        self._dibujar_cuerpo_enemigo(pantalla)
        self._dibujar_barra_vida(pantalla)
        self._dibujar_efectos_estado(pantalla)
    
    def _dibujar_cuerpo_enemigo(self, pantalla: pygame.Surface):
        desplazamiento_tiempo = pygame.time.get_ticks() + self._desplazamiento_animacion
        factor_animacion = math.sin(desplazamiento_tiempo * 0.005) * 0.1 + 1.0
        tamaño_animado = int(self._tamaño * factor_animacion)
        # --- EFECTO VISUAL DE DAÑO ---
        color = (255, 0, 0) if self._recibio_daño else self._color
        pygame.draw.circle(
            pantalla, 
            color, 
            (int(self.x), int(self.y)), 
            tamaño_animado
        )
        pygame.draw.circle(
            pantalla, 
            (0, 0, 0), 
            (int(self.x), int(self.y)), 
            tamaño_animado, 
            2
        )
    
    def _dibujar_barra_vida(self, pantalla: pygame.Surface):
        ancho_barra = 30
        alto_barra = 5
        porcentaje_vida = self.obtener_porcentaje_vida()
        barra_x = self.x - ancho_barra // 2
        barra_y = self.y - self._tamaño - 10
        pygame.draw.rect(pantalla, (255, 0, 0), 
                        (barra_x, barra_y, ancho_barra, alto_barra))
        if porcentaje_vida > 0:
            pygame.draw.rect(pantalla, (0, 255, 0), 
                            (barra_x, barra_y, ancho_barra * porcentaje_vida, alto_barra))
        pygame.draw.rect(pantalla, (0, 0, 0), 
                        (barra_x, barra_y, ancho_barra, alto_barra), 1)
    
    def _dibujar_efectos_estado(self, pantalla: pygame.Surface):
        efecto_y = self.y + self._tamaño + 5
        if self._esta_ralentizado:
            pygame.draw.circle(pantalla, (0, 0, 255), 
                             (int(self.x - 10), int(efecto_y)), 3)

class EnemigoBasico(Enemigo):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, vida=50, velocidad=50, recompensa=10, tipo_enemigo="basico")
        self._tamaño = 15
        
    def _calcular_resistencia_daño(self, daño: int, tipo_daño: str) -> int:
        return daño

class EnemigoRapido(Enemigo):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, vida=30, velocidad=80, recompensa=15, tipo_enemigo="rapido")
        self._tamaño = 12
        self._impulso_velocidad = lambda: random.uniform(0.9, 1.1)
    
    def obtener_velocidad_actual(self) -> float:
        velocidad_base = super().obtener_velocidad_actual()
        return velocidad_base * self._impulso_velocidad()
    
    def _calcular_resistencia_daño(self, daño: int, tipo_daño: str) -> int:
        if tipo_daño == "explosivo":
            return int(daño * 1.2)
        return daño
    
    def _dibujar_cuerpo_enemigo(self, pantalla: pygame.Surface):
        super()._dibujar_cuerpo_enemigo(pantalla)
        posiciones_rastro = [
            (self.x - 5, self.y),
            (self.x - 10, self.y),
            (self.x - 15, self.y)
        ]
        for i, pos in enumerate(posiciones_rastro):
            alfa = 100 - (i * 30)
            color_rastro = (*self._color[:3], max(0, alfa))
            pygame.draw.circle(pantalla, self._color, (int(pos[0]), int(pos[1])), 
                             max(1, self._tamaño - i * 2))

class EnemigoTanque(Enemigo):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, vida=120, velocidad=30, recompensa=25, tipo_enemigo="tanque")
        self._tamaño = 20
        self._armadura = 5
        self._reduccion_armadura = lambda daño: max(1, daño - self._armadura)
    
    def _calcular_resistencia_daño(self, daño: int, tipo_daño: str) -> int:
        if tipo_daño == "perforante":
            return daño
        daño_reducido = self._reduccion_armadura(daño)
        return daño_reducido
    
    def recibir_daño(self, daño: int, tipo_daño: str = "normal") -> bool:
        daño_original = daño
        resultado = super().recibir_daño(daño, tipo_daño)
        daño_final = self._calcular_resistencia_daño(daño_original, tipo_daño)
        if daño_final < daño_original:
            self._mostrar_efecto_armadura = True
        return resultado
    
    def _dibujar_cuerpo_enemigo(self, pantalla: pygame.Surface):
        super()._dibujar_cuerpo_enemigo(pantalla)
        radio_anillo_armadura = self._tamaño + 3
        pygame.draw.circle(pantalla, (128, 128, 128), 
                         (int(self.x), int(self.y)), radio_anillo_armadura, 2)

FABRICAS_ENEMIGOS = {
    'basico': lambda x, y: EnemigoBasico(x, y),
    'rapido': lambda x, y: EnemigoRapido(x, y),
    'tanque': lambda x, y: EnemigoTanque(x, y),
}

def crear_enemigo(tipo_enemigo: str, x: float, y: float) -> Enemigo:
    if tipo_enemigo not in FABRICAS_ENEMIGOS:
        raise ExcepcionGeneracionEnemigo(
            f"Tipo de enemigo desconocido: {tipo_enemigo}",
            tipo_enemigo=tipo_enemigo,
            posicion_generacion=(x, y)
        )
    return FABRICAS_ENEMIGOS[tipo_enemigo](x, y)

def filtrar_enemigos_por_condicion(enemigos: List[Enemigo], 
                                 condicion: Callable[[Enemigo], bool]) -> List[Enemigo]:
    return list(filter(condicion, enemigos))

def obtener_enemigos_vida_baja(enemigos: List[Enemigo], umbral: float = 0.3) -> List[Enemigo]:
    return filtrar_enemigos_por_condicion(
        enemigos, 
        lambda enemigo: enemigo.obtener_porcentaje_vida() < umbral
    )

def obtener_enemigos_en_rango(enemigos: List[Enemigo], centro: Tuple[float, float], 
                            radio_rango: float) -> List[Enemigo]:
    return filtrar_enemigos_por_condicion(
        enemigos,
        lambda enemigo: enemigo.distancia_a_punto(centro) <= radio_rango
    )

def obtener_enemigos_por_tipo(enemigos: List[Enemigo], tipo_enemigo: str) -> List[Enemigo]:
    return filtrar_enemigos_por_condicion(
        enemigos,
        lambda enemigo: enemigo.tipo_enemigo == tipo_enemigo
    )

if __name__ == "__main__":
    print("Probando Clases de Enemigos...")
    basico = EnemigoBasico(100, 100)
    rapido = EnemigoRapido(200, 200)
    tanque = EnemigoTanque(300, 300)
    enemigos = [basico, rapido, tanque]
    for enemigo in enemigos:
        print(f"{enemigo.tipo_enemigo}: Vida={enemigo.vida}, Velocidad={enemigo.velocidad}, Recompensa={enemigo.recompensa}")
        enemigo.recibir_daño(50)
        print(f"Después del daño: Vida={enemigo.vida}")
    vida_baja = obtener_enemigos_vida_baja(enemigos, 0.8)
    print(f"Enemigos con vida baja: {[e.tipo_enemigo for e in vida_baja]}")
    enemigos_tanque = obtener_enemigos_por_tipo(enemigos, "tanque")
    print(f"Enemigos tanque: {[e.tipo_enemigo for e in enemigos_tanque]}")
    print("¡Prueba de enemigos completada!")