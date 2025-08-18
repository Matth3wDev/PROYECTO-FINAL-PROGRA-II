import pygame
import math
from Objetos import Objetos
from typing import List, Optional


class torres(Objetos):
    """
    Clase base para todas las torres del juego.
    Hereda de Objetos para mantener la estructura POO.
    """
    
    def __init__(self, x: float, y: float, nombre: str = "Torre Base", 
                 costo: int = 100, rango: float = 150, cadencia_fuego: float = 1500,
                 daño: int = 10, imagen_torre: str = "imagen"):
        super().__init__(x, y)
        
        
        self.nombre = nombre
        self.costo = costo
        self.rango = rango  
        self.daño = daño
        self.cadencia_fuego = cadencia_fuego  
        self.imagen_torre = imagen_torre
        
        
        self.ultimo_disparo = 0
        self.nivel = 1
        self.objetivo_actual = None
        
        
        self.color = (0, 100, 255)  
        self.radio_visual = 25
        self.mostrar_rango = False
        
        
        self.enemigos_eliminados = 0
        self.daño_total_infligido = 0

    @property
    def puede_disparar(self) -> bool:
        """Verifica si la torre puede disparar basado en la cadencia de fuego."""
        tiempo_actual = pygame.time.get_ticks()
        return tiempo_actual - self.ultimo_disparo >= self.cadencia_fuego

    def encontrar_objetivo(self, enemigos: List) -> Optional[object]:
        """
        Busca el enemigo más cercano dentro del alcance.
        
        Args:
            enemigos: Lista de enemigos en el juego
            
        Returns:
            El enemigo más cercano o None si no hay objetivos
        """
        objetivo_mas_cercano = None
        distancia_minima = self.rango

        for enemigo in enemigos:
            if hasattr(enemigo, 'activo') and enemigo.activo:
                
                distancia = math.sqrt((self.x - enemigo.x)**2 + (self.y - enemigo.y)**2)
                
                if distancia <= self.rango and distancia < distancia_minima:
                    objetivo_mas_cercano = enemigo
                    distancia_minima = distancia
        
        self.objetivo_actual = objetivo_mas_cercano
        return objetivo_mas_cercano

    def disparar(self, objetivo, lista_proyectiles: List):
        """
        Dispara un proyectil al enemigo objetivo.
        
        Args:
            objetivo: Enemigo objetivo
            lista_proyectiles: Lista donde agregar el nuevo proyectil
        """
        if not self.puede_disparar or not objetivo:
            return False
        
        
        from misiles import misiles
        
        
        nuevo_proyectil = misiles(self.x, self.y, objetivo.x, objetivo.y, self.daño)
        lista_proyectiles.append(nuevo_proyectil)
        
        
        self.ultimo_disparo = pygame.time.get_ticks()
        
        return True

    def actualizar(self, dt: float):
        """
        Actualiza la lógica de la torre.
        
        Args:
            dt: Delta time en milisegundos
        """
        
        pass

    def dibujar(self, pantalla: pygame.Surface):
        """
        Dibuja la torre y opcionalmente su rango en la pantalla.
        
        Args:
            pantalla: Superficie de pygame donde dibujar
        """
        
        if self.mostrar_rango:
            pygame.draw.circle(pantalla, (255, 255, 255, 50), 
                             (int(self.x), int(self.y)), int(self.rango), 2)
        
        
        pygame.draw.circle(pantalla, self.color, 
                         (int(self.x), int(self.y)), self.radio_visual)
        
        
        pygame.draw.circle(pantalla, (255, 255, 255), 
                         (int(self.x), int(self.y)), self.radio_visual, 3)
        
        
        if self.objetivo_actual and hasattr(self.objetivo_actual, 'x'):
            
            dx = self.objetivo_actual.x - self.x
            dy = self.objetivo_actual.y - self.y
            angulo = math.atan2(dy, dx)
            
            
            cañon_length = self.radio_visual + 10
            fin_x = self.x + math.cos(angulo) * cañon_length
            fin_y = self.y + math.sin(angulo) * cañon_length
            
            pygame.draw.line(pantalla, (50, 50, 50), 
                           (int(self.x), int(self.y)), 
                           (int(fin_x), int(fin_y)), 5)

    def mejorar(self) -> bool:
        """
        Mejora la torre aumentando sus estadísticas.
        
        Returns:
            True si la mejora fue exitosa, False en caso contrario
        """
        if self.nivel >= 5:  
            return False
        
        self.nivel += 1
        self.daño = int(self.daño * 1.3)  
        self.rango = int(self.rango * 1.1)  
        self.cadencia_fuego = max(200, int(self.cadencia_fuego * 0.85))  
        
        return True

    def obtener_costo_mejora(self) -> int:
        """Retorna el costo de mejorar la torre."""
        return int(self.costo * (self.nivel * 0.8))

    def obtener_valor_venta(self) -> int:
        """Retorna el valor de venta de la torre."""
        valor_base = int(self.costo * 0.7)  
        valor_mejoras = sum(int(self.costo * (i * 0.8) * 0.5) for i in range(1, self.nivel))
        return valor_base + valor_mejoras

    def seleccionar(self):
        """Marca la torre como seleccionada."""
        self.mostrar_rango = True

    def deseleccionar(self):
        """Desmarca la torre como seleccionada."""
        self.mostrar_rango = False

    def obtener_info(self) -> dict:
        """
        Retorna información detallada de la torre.
        
        Returns:
            Diccionario con la información de la torre
        """
        return {
            'nombre': self.nombre,
            'nivel': self.nivel,
            'daño': self.daño,
            'rango': self.rango,
            'cadencia_fuego': self.cadencia_fuego,
            'costo': self.costo,
            'enemigos_eliminados': self.enemigos_eliminados,
            'daño_total': self.daño_total_infligido,
            'valor_venta': self.obtener_valor_venta(),
            'costo_mejora': self.obtener_costo_mejora() if self.nivel < 5 else None
        }

    def __str__(self) -> str:
        return f"{self.nombre} Nv.{self.nivel} (Daño: {self.daño}, Rango: {self.rango})"



if __name__ == "__main__":
    print("Probando clase torres...")
    
    
    torre_prueba = torres(300, 300, "Torre de Prueba", costo=150, 
                         rango=200, daño=25)
    
    print(f"Torre creada: {torre_prueba}")
    print(f"Información de la torre:")
    
    info = torre_prueba.obtener_info()
    for clave, valor in info.items():
        print(f"  {clave}: {valor}")
    
    
    print(f"\nMejorando torre...")
    if torre_prueba.mejorar():
        print(f"Torre mejorada: {torre_prueba}")
        print(f"Nuevo costo de mejora: ${torre_prueba.obtener_costo_mejora()}")
    
    print("Prueba de torres completada!")