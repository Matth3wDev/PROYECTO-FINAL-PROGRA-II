import pygame
import math
from Objetos import Objetos

class misiles(Objetos):
    def __init__(self, x: float, y: float, target_x: float, target_y: float, damage: int = 25):
        super().__init__(x, y)
        
        
        self.start_x = x
        self.start_y = y
        
        
        self.target_x = target_x
        self.target_y = target_y
        
        
        self.damage = damage
        self.speed = 200.0 
        self.activo = True
        
        
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            self.direction_x = dx / distance
            self.direction_y = dy / distance
        else:
            self.direction_x = 0
            self.direction_y = 0
        
        
        self.color = (255, 100, 0)  
        self.radius = 3

    def actualizar(self, dt: float):
        """Actualiza la posición del misil."""
        if not self.activo:
            return
        
        
        movement_distance = self.speed * (dt / 1000.0)
        self.x += self.direction_x * movement_distance
        self.y += self.direction_y * movement_distance
        
        
        distance_to_target = math.sqrt((self.x - self.target_x)**2 + (self.y - self.target_y)**2)
        
        if distance_to_target < 10:  
            self.activo = False
        
        
        if self.x < 0 or self.x > 1200 or self.y < 0 or self.y > 800:
            self.activo = False

    def dibujar(self, pantalla: pygame.Surface):
        """Dibuja el misil en pantalla."""
        if self.activo:
            
            pygame.draw.circle(pantalla, self.color, (int(self.x), int(self.y)), self.radius)
            
            
            tail_length = 15
            tail_x = self.x - self.direction_x * tail_length
            tail_y = self.y - self.direction_y * tail_length
            
            
            tail_color = (self.color[0] // 2, self.color[1] // 2, self.color[2] // 2)
            pygame.draw.line(pantalla, tail_color, (int(tail_x), int(tail_y)), (int(self.x), int(self.y)), 2)

    def obtener_damage(self) -> int:
        """Retorna el daño del misil."""
        return self.damage

    def colisiona_con_enemigo(self, enemigo) -> bool:
        """Verifica si el misil colisiona con un enemigo."""
        if not self.activo or not enemigo.activo:
            return False
        
        distance = math.sqrt((self.x - enemigo.x)**2 + (self.y - enemigo.y)**2)
        return distance <= 15  

    def __str__(self) -> str:
        return f"Misil(pos=({self.x:.1f}, {self.y:.1f}), objetivo=({self.target_x}, {self.target_y}), activo={self.activo})"



class MisilTeledirigido(misiles):
    """Misil que puede seguir objetivos móviles."""
    
    def __init__(self, x: float, y: float, objetivo_enemigo, damage: int = 50):
        
        super().__init__(x, y, objetivo_enemigo.x, objetivo_enemigo.y, damage)
        self.objetivo_enemigo = objetivo_enemigo
        self.velocidad_giro = 0.05  
        self.color = (255, 0, 0)  
    
    def actualizar(self, dt: float):
        """Actualiza la posición del misil teledirigido."""
        if not self.activo:
            return
        
        
        if hasattr(self.objetivo_enemigo, 'activo') and self.objetivo_enemigo.activo:
            
            dx = self.objetivo_enemigo.x - self.x
            dy = self.objetivo_enemigo.y - self.y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                new_direction_x = dx / distance
                new_direction_y = dy / distance
                
                
                self.direction_x += (new_direction_x - self.direction_x) * self.velocidad_giro
                self.direction_y += (new_direction_y - self.direction_y) * self.velocidad_giro
                
                
                dir_magnitude = math.sqrt(self.direction_x**2 + self.direction_y**2)
                if dir_magnitude > 0:
                    self.direction_x /= dir_magnitude
                    self.direction_y /= dir_magnitude
        
        
        super().actualizar(dt)
        
        
        if (hasattr(self.objetivo_enemigo, 'activo') and 
            self.objetivo_enemigo.activo and 
            self.colisiona_con_enemigo(self.objetivo_enemigo)):
            self.activo = False


if __name__ == "__main__":
    
    print("Probando clase misiles...")
    
    
    misil = misiles(100, 100, 200, 200, 25)
    print(f"Misil creado: {misil}")
    
    
    for i in range(5):
        misil.actualizar(16.67)  
        print(f"Frame {i+1}: {misil}")
    
    print("Prueba de misiles completada!")