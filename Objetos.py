from abc import ABC, abstractmethod
import pygame

class Objetos(ABC):
    
    
    def __init__(self, x: float, y: float):
        """
        Constructor de la clase base ObjetoJuego.
        
        Args:
            x (float): Posición inicial en el eje X
            y (float): Posición inicial en el eje Y
        """
        # Encapsulamiento: propiedades protegidas de la clase
        self._x = float(x)
        self._y = float(y)
        self._activo = True
        
        # ID único para cada objeto (útil para depuración)
        import time
        self._id = int(time.time() * 1000000) % 1000000
    
    # Propiedades usando decoradores (getter/setter) - Encapsulamiento
    @property
    def x(self) -> float:
        """Getter para la posición X"""
        return self._x
    
    @x.setter
    def x(self, valor: float):
        """Setter para la posición X con validación"""
        self._x = float(valor)
    
    @property
    def y(self) -> float:
        """Getter para la posición Y"""
        return self._y
    
    @y.setter
    def y(self, valor: float):
        """Setter para la posición Y con validación"""
        self._y = float(valor)
    
    @property
    def activo(self) -> bool:
        """Getter para el estado activo"""
        return self._activo
    
    @activo.setter
    def activo(self, valor: bool):
        """Setter para el estado activo"""
        self._activo = bool(valor)
    
    @property
    def id(self) -> int:
        """ID único del objeto (solo lectura)"""
        return self._id
    
    def obtener_posicion(self) -> tuple:
        """
        Obtener la posición como tupla.
        
        Returns:
            tuple: (x, y) posición del objeto
        """
        return (self._x, self._y)
    
    def establecer_posicion(self, x: float, y: float):
        """
        Establecer nueva posición del objeto.
        
        Args:
            x (float): Nueva posición X
            y (float): Nueva posición Y
        """
        self._x = float(x)
        self._y = float(y)
    
    def distancia_a(self, otro_objeto) -> float:
        """
        Calcular distancia a otro objeto ObjetoJuego.
        
        Args:
            otro_objeto (ObjetoJuego): Otro objeto del juego
            
        Returns:
            float: Distancia euclidiana entre los objetos
        """
        if not isinstance(otro_objeto, Objetos):
            raise TypeError("El objeto debe ser una instancia de ObjetoJuego")
        
        import math
        dx = self._x - otro_objeto.x
        dy = self._y - otro_objeto.y
        return math.sqrt(dx * dx + dy * dy)
    
    def esta_colisionando_con(self, otro_objeto, radio_colision: float = 10.0) -> bool:
        """
        Verificar si hay colisión con otro objeto.
        
        Args:
            otro_objeto (ObjetoJuego): Otro objeto del juego
            radio_colision (float): Radio de colisión
            
        Returns:
            bool: True si hay colisión, False en caso contrario
        """
        if not isinstance(otro_objeto, Objetos):
            return False
            
        return self.distancia_a(otro_objeto) <= radio_colision
    
    def desactivar(self):
        """Desactivar el objeto (marcarlo para eliminación)"""
        self._activo = False
    
    def reactivar(self):
        """Reactivar el objeto"""
        self._activo = True
    
    # Métodos abstractos que DEBEN ser implementados por las subclases
    @abstractmethod
    def actualizar(self, dt: float):
        """
        Actualizar la lógica del objeto.
        
        Este es un método abstracto que debe ser implementado por todas
        las subclases. Define cómo el objeto actualiza su estado cada frame.
        
        Args:
            dt (float): Delta time - tiempo transcurrido desde la última actualización
        """
        pass
    
    @abstractmethod
    def dibujar(self, pantalla: pygame.Surface):
        """
        Dibujar el objeto en pantalla.
        
        Este es un método abstracto que debe ser implementado por todas
        las subclases. Define cómo el objeto se renderiza en pantalla.
        
        Args:
            pantalla (pygame.Surface): Superficie donde dibujar el objeto
        """
        pass
    
    def __str__(self) -> str:
        """Representación string del objeto para depuración"""
        return f"{self.__class__.__name__}(id={self._id}, pos=({self._x:.1f}, {self._y:.1f}), activo={self._activo})"
    
    def __repr__(self) -> str:
        """Representación técnica del objeto"""
        return f"{self.__class__.__name__}(x={self._x}, y={self._y})"
    
    def __eq__(self, otro) -> bool:
        """Comparación de igualdad basada en ID"""
        if not isinstance(otro, Objetos):
            return False
        return self._id == otro._id
    
    def __hash__(self) -> int:
        """Hash del objeto basado en ID (para usar en sets/dicts)"""
        return hash(self._id)


class ObjetoJuegoAnimado(Objetos):
    """
    Clase base para objetos animados.
    
    Extiende ObjetoJuego añadiendo funcionalidad de animación.
    Demuestra herencia de la clase abstracta.
    """
    
    def __init__(self, x: float, y: float):
        """
        Constructor para objetos animados.
        
        Args:
            x (float): Posición inicial X
            y (float): Posición inicial Y
        """
        super().__init__(x, y)
        
        # Propiedades de animación
        self._frame_animacion = 0
        self._velocidad_animacion = 1.0
        self._temporizador_animacion = 0.0
        self._frames_maximos = 1
    
    @property
    def frame_animacion(self) -> int:
        """Frame actual de animación"""
        return self._frame_animacion
    
    @property
    def velocidad_animacion(self) -> float:
        """Velocidad de animación"""
        return self._velocidad_animacion
    
    @velocidad_animacion.setter
    def velocidad_animacion(self, velocidad: float):
        """Establecer velocidad de animación"""
        self._velocidad_animacion = max(0.1, float(velocidad))
    
    def establecer_frames_animacion(self, frames_maximos: int):
        """
        Configurar número máximo de frames de animación.
        
        Args:
            frames_maximos (int): Número de frames de la animación
        """
        self._frames_maximos = max(1, int(frames_maximos))
        self._frame_animacion = 0
    
    def actualizar_animacion(self, dt: float):
        """
        Actualizar la animación del objeto.
        
        Args:
            dt (float): Delta time en milisegundos
        """
        self._temporizador_animacion += dt
        
        # Cambiar frame cada cierto tiempo basado en la velocidad
        duracion_frame = 1000.0 / self._velocidad_animacion  # ms por frame
        
        if self._temporizador_animacion >= duracion_frame:
            self._temporizador_animacion = 0
            self._frame_animacion = (self._frame_animacion + 1) % self._frames_maximos
    
    def reiniciar_animacion(self):
        """Reiniciar la animación al frame 0"""
        self._frame_animacion = 0
        self._temporizador_animacion = 0.0
    
    # Estos métodos siguen siendo abstractos y deben implementarse
    @abstractmethod
    def actualizar(self, dt: float):
        """Método abstracto que debe incluir actualizar_animacion"""
        pass
    
    @abstractmethod
    def dibujar(self, pantalla: pygame.Surface):
        """Método abstracto para dibujar el objeto animado"""
        pass


# Ejemplo de uso y pruebas (opcional)
if __name__ == "__main__":
    # Este código solo se ejecuta si el archivo se ejecuta directamente
    print("Probando ObjetoJuego...")
    
    # No podemos instanciar ObjetoJuego directamente porque es abstracta
    try:
        # obj = ObjetoJuego(100, 100)  # Esto daría error
        pass
    except TypeError as e:
        print(f"Error esperado: {e}")
    
    # Podríamos crear una implementación de prueba
    class ObjetoPrueba(Objetos):
        def __init__(self, x, y):
            super().__init__(x, y)
        
        def actualizar(self, dt):
            # Implementación simple de prueba
            self.x += 1
        
        def dibujar(self, pantalla):
            # Implementación simple de prueba
            print(f"Dibujando {self} en ({self.x}, {self.y})")
    
    # Ahora sí podemos crear instancias
    obj_prueba1 = ObjetoPrueba(100, 100)
    obj_prueba2 = ObjetoPrueba(150, 150)
    
    print(f"Objeto 1: {obj_prueba1}")
    print(f"Objeto 2: {obj_prueba2}")
    print(f"Distancia entre objetos: {obj_prueba1.distancia_a(obj_prueba2):.2f}")
    print(f"¿Están colisionando? {obj_prueba1.esta_colisionando_con(obj_prueba2, 60)}")
    
    print("¡ObjetoJuego creado exitosamente!")