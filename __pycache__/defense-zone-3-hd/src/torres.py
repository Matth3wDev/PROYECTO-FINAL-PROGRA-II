class torres:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def dibujar(self, pantalla):
        pass

    def actualizar(self):
        pass

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