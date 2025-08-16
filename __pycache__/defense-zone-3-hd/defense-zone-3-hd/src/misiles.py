class Misil:
    def __init__(self, x: int, y: int, objetivo_x: int, objetivo_y: int):
        self.x = x
        self.y = y
        self.objetivo_x = objetivo_x
        self.objetivo_y = objetivo_y
        self.velocidad = 5
        self.daño = 50

    def mover(self):
        dx = self.objetivo_x - self.x
        dy = self.objetivo_y - self.y
        distancia = (dx**2 + dy**2)**0.5
        if distancia > 0:
            dx /= distancia
            dy /= distancia
            self.x += dx * self.velocidad
            self.y += dy * self.velocidad

    def ha_impactado(self) -> bool:
        return self.x == self.objetivo_x and self.y == self.objetivo_y

    def obtener_posicion(self):
        return self.x, self.y