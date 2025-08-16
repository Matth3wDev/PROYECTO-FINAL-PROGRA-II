import pygame
import math

class gestor_recursos:
    def __init__(self, initial_money, initial_lives):
        self.money = initial_money
        self.lives = initial_lives

    def can_afford(self, cost):
        """Verifica si el jugador tiene suficiente dinero."""
        return self.money >= cost

    def spend_money(self, cost):
        """Resta dinero."""
        self.money -= cost

    def earn_money(self, amount):
        """Suma dinero."""
        self.money += amount

    def lose_life(self):
        """Resta una vida."""
        self.lives -= 1
        if self.lives <= 0:
            print("¡Fin del juego!") # Puedes reemplazar esto con tu lógica de Game Over
            return True # Retorna True si el juego termina
        return False
        
    def draw_ui(self, screen):
        """Dibuja la información de la UI en la pantalla."""
        font = pygame.font.SysFont("Arial", 24)
        money_text = font.render(f"Dinero: ${self.money}", True, (255, 255, 255))
        lives_text = font.render(f"Vidas: {self.lives}", True, (255, 255, 255))
        screen.blit(money_text, (10, 10))
        screen.blit(lives_text, (10, 40))