class Enemigo:
    def __init__(self, x: int, y: int, vida: int, velocidad: float):
        self.x = x
        self.y = y
        self.vida = vida
        self.velocidad = velocidad
        self.activo = True

    def mover(self):
        if self.activo:
            self.x += self.velocidad

    def recibir_dano(self, dano: int):
        self.vida -= dano
        if self.vida <= 0:
            self.activo = False

class EnemigoBasico(Enemigo):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, vida=100, velocidad=1.0)

class EnemigoRapido(Enemigo):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, vida=50, velocidad=2.0)

class EnemigoTanque(Enemigo):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, vida=200, velocidad=0.5)