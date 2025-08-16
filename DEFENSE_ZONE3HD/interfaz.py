import pygame

BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
ROJO = (255, 0, 0)
GRIS_OSCURO = (64, 64, 64)
AZUL = (0, 0, 255)

class Boton:
    def __init__(self, x, y, ancho, alto, texto, color_fondo, color_texto, fuente):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.texto = texto
        self.color_fondo = color_fondo
        self.color_texto = color_texto
        self.fuente = fuente

    def dibujar(self, pantalla):
        pygame.draw.rect(pantalla, self.color_fondo, self.rect)
        pygame.draw.rect(pantalla, NEGRO, self.rect, 2)
        texto_render = self.fuente.render(self.texto, True, self.color_texto)
        pantalla.blit(
            texto_render,
            (
                self.rect.x + (self.rect.width - texto_render.get_width()) // 2,
                self.rect.y + (self.rect.height - texto_render.get_height()) // 2,
            ),
        )

    def esta_sobre(self, pos):
        return self.rect.collidepoint(pos)

class Interfaz:
    def __init__(self, pantalla, fuente, fuente_pequeña):
        self.pantalla = pantalla
        self.fuente = fuente
        self.fuente_pequeña = fuente_pequeña
        self.boton_salir_menu = Boton(1050, 700, 200, 50, "Salir", ROJO, BLANCO, fuente)
        self.boton_salir_juego = Boton(1050, 700, 200, 50, "Menu", AZUL, BLANCO, fuente)

    def dibujar_menu(self):
        self.boton_salir_menu.dibujar(self.pantalla)

    def dibujar_juego(self):
        self.boton_salir_juego.dibujar(self.pantalla)

    def manejar_evento(self, evento, estado_juego):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pos = evento.pos
            if estado_juego == "MENU":
                if self.boton_salir_menu.esta_sobre(pos):
                    return "SALIR"
            elif estado_juego == "JUGANDO":
                if self.boton_salir_juego.esta_sobre(pos):
                    return "MENU"
        return None