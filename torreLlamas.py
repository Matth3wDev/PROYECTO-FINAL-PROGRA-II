from torres import torre

class torresLlamas(torre):
    def __init__(self, x, y):
        super().__init__(
            x=x,
            y=y,
            nombre="Torre de lanza llamas",
            costo=75,
            rango=200,
            cadencia_fuego=1500, 
            daño=80,
            imagen_torre="imagen"
        )