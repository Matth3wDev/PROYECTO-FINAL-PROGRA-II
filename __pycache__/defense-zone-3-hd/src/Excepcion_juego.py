class Excepcion_juego(Exception):
    pass

class ExcepcionRecursosInsuficientes(Excepcion_juego):
    def __init__(self, mensaje: str):
        super().__init__(mensaje)

class ExcepcionColocacionTorre(Excepcion_juego):
    def __init__(self, mensaje: str):
        super().__init__(mensaje)