import pygame
import math
import threading
import time
from enum import Enum
from typing import List, Tuple

# Colores mejorados para mejor legibilidad
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
VERDE = (34, 139, 34)  # Verde más oscuro
AZUL = (25, 25, 112)   # Azul marino
AMARILLO = (255, 215, 0)
ROJO = (220, 20, 60)
VERDE_CLARO = (152, 251, 152)  # Verde menta claro
AZUL_CLARO = (230, 240, 255)   # Azul muy claro
GRIS_CLARO = (248, 248, 255)   # Casi blanco
GRIS_TEXTO = (64, 64, 64)      # Gris oscuro para texto
MORADO = (75, 0, 130)

class FaseTutorial(Enum):
    INICIO = 0
    INTERFAZ_BASICA = 1
    COLOCAR_TORRE = 2
    TIPOS_TORRES = 3
    PRIMER_ENEMIGO = 4
    RECURSOS_DINERO = 5
    TIPOS_ENEMIGOS = 6
    ESTRATEGIA = 7
    OLEADAS = 8
    VICTORIA = 9

class ObjetivoTutorial:
    def __init__(self, descripcion: str, completado: bool = False):
        self.descripcion = descripcion
        self.completado = completado

    def completar(self):
        self.completado = True

class TutorialInteractivo:
    def __init__(self, juego_principal):
        self.juego = juego_principal
        self.activo = False
        self.fase_actual = FaseTutorial.INICIO
        
        # Fuentes optimizadas para legibilidad
        self.fuente_titulo = pygame.font.SysFont("arial", 16, bold=True)
        self.fuente_texto = pygame.font.SysFont("arial", 13)
        self.fuente_pequeña = pygame.font.SysFont("arial", 12)
        
        self.objetivos_actuales: List[ObjetivoTutorial] = []
        self.mensaje_principal = ""
        self.mensaje_secundario = ""
        self.puede_continuar = False
        self.torres_colocadas = 0
        self.enemigos_tutorial_spawneados = 0
        self.tiempo_fase_inicio = 0

    def iniciar_tutorial(self):
        self.activo = True
        self.fase_actual = FaseTutorial.INICIO
        self.juego.gestor_recursos.recursos = {"dinero": 300, "vidas": 10}
        self.juego.torres.clear()
        self.juego.enemigos.clear()
        self.juego.proyectiles.clear()
        self.torres_colocadas = 0
        self.enemigos_tutorial_spawneados = 0
        self.tiempo_fase_inicio = pygame.time.get_ticks()
        self._cargar_fase()

    def _cargar_fase(self):
        self.objetivos_actuales.clear()
        self.puede_continuar = False
        self.tiempo_fase_inicio = pygame.time.get_ticks()
        
        if self.fase_actual == FaseTutorial.INICIO:
            self.mensaje_principal = "¡Bienvenido al Tutorial!"
            self.mensaje_secundario = "Aprende Defense Zone 3 HD paso a paso"
            self.objetivos_actuales.append(ObjetivoTutorial("Presiona ESPACIO para comenzar"))
            
        elif self.fase_actual == FaseTutorial.INTERFAZ_BASICA:
            self.mensaje_principal = "Interfaz del Juego"
            self.mensaje_secundario = "Observa los elementos de la pantalla"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Dinero (arriba izquierda): Para torres"),
                ObjetivoTutorial("Vidas (arriba izquierda): Si llegan a 0, pierdes"),
                ObjetivoTutorial("Teclas 1,2,3: Tipos de torre")
            ])
            
        elif self.fase_actual == FaseTutorial.COLOCAR_TORRE:
            self.mensaje_principal = "Coloca tu Primera Torre"
            self.mensaje_secundario = "Presiona '1' para Torre Cañón, luego clic"
            self.objetivos_actuales.append(ObjetivoTutorial("Coloca una Torre Cañón ($50)"))
            
        elif self.fase_actual == FaseTutorial.TIPOS_TORRES:
            self.mensaje_principal = "Tipos de Torres"
            self.mensaje_secundario = "Cada torre tiene características únicas"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Cañón (1): $50 - Equilibrada"),
                ObjetivoTutorial("Misil (2): $100 - Alto daño, lenta"), 
                ObjetivoTutorial("Láser (3): $75 - Rápida, menor daño")
            ])
            
        elif self.fase_actual == FaseTutorial.PRIMER_ENEMIGO:
            self.mensaje_principal = "¡Tu Primer Enemigo!"
            self.mensaje_secundario = "Las torres atacan automáticamente"
            self.objetivos_actuales.append(ObjetivoTutorial("Observa cómo tu torre dispara"))
            self._generar_enemigo_tutorial('basico')
            
        elif self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            self.mensaje_principal = "Gestión de Recursos"
            self.mensaje_secundario = "Ganas dinero eliminando enemigos"
            dinero_actual = self.juego.gestor_recursos.obtener('dinero')
            self.objetivos_actuales.extend([
                ObjetivoTutorial(f"Dinero actual: ${dinero_actual}"),
                ObjetivoTutorial("Cada enemigo da dinero al morir"),
                ObjetivoTutorial("Usa el dinero para más torres")
            ])
            
        elif self.fase_actual == FaseTutorial.TIPOS_ENEMIGOS:
            self.mensaje_principal = "Tipos de Enemigos"
            self.mensaje_secundario = "Diferentes enemigos, estrategias diferentes"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Rojos: Básicos (50 HP, velocidad normal)"),
                ObjetivoTutorial("Amarillos: Rápidos (30 HP, veloces)"),
                ObjetivoTutorial("Grises: Tanques (120 HP, lentos, duros)")
            ])
            self._generar_enemigos_variados()
            
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            self.mensaje_principal = "Estrategia Básica"
            self.mensaje_secundario = "Coloca torres en puntos estratégicos"
            self.objetivos_actuales.extend([
                ObjetivoTutorial("Coloca torres cerca de curvas"),
                ObjetivoTutorial("Usa diferentes tipos de torres"),
                ObjetivoTutorial("Ten al menos 3 torres activas")
            ])
            
        elif self.fase_actual == FaseTutorial.OLEADAS:
            self.mensaje_principal = "¡Oleada de Enemigos!"
            self.mensaje_secundario = "Defiende contra múltiples enemigos"
            self.objetivos_actuales.append(ObjetivoTutorial("Sobrevive a la oleada tutorial"))
            self._iniciar_oleada_tutorial()
            
        elif self.fase_actual == FaseTutorial.VICTORIA:
            self.mensaje_principal = "¡Tutorial Completado!"
            self.mensaje_secundario = "Ya dominas lo básico del juego"
            self.objetivos_actuales.append(ObjetivoTutorial("Presiona ESC para volver al menú"))

    def _generar_enemigo_tutorial(self, tipo: str):
        try:
            from Enemigo import EnemigoBasico, EnemigoRapido, EnemigoTanque
            clases_enemigos = {
                'basico': EnemigoBasico,
                'rapido': EnemigoRapido,
                'tanque': EnemigoTanque
            }
            if tipo in clases_enemigos:
                enemigo = clases_enemigos[tipo](self.juego.camino[0][0], self.juego.camino[0][1])
                enemigo.ruta = self.juego.camino
                self.juego.enemigos.append(enemigo)
                self.enemigos_tutorial_spawneados += 1
        except Exception as e:
            print(f"Error generando enemigo tutorial: {e}")

    def _generar_enemigos_variados(self):
        tipos = ['basico', 'rapido', 'tanque']
        try:
            from Enemigo import EnemigoBasico, EnemigoRapido, EnemigoTanque
            clases_enemigos = {
                'basico': EnemigoBasico,
                'rapido': EnemigoRapido,
                'tanque': EnemigoTanque
            }
            for i, tipo in enumerate(tipos):
                if tipo in clases_enemigos:
                    x = self.juego.camino[0][0] - (i * 60)
                    enemigo = clases_enemigos[tipo](x, self.juego.camino[0][1])
                    enemigo.ruta = self.juego.camino
                    self.juego.enemigos.append(enemigo)
        except Exception as e:
            print(f"Error generando enemigos variados: {e}")

    def _iniciar_oleada_tutorial(self):
        def generar_oleada():
            tipos = ['basico', 'basico', 'rapido', 'tanque', 'basico']
            try:
                from Enemigo import EnemigoBasico, EnemigoRapido, EnemigoTanque
                clases_enemigos = {
                    'basico': EnemigoBasico,
                    'rapido': EnemigoRapido,
                    'tanque': EnemigoTanque
                }
                for i, tipo in enumerate(tipos):
                    time.sleep(1.5)
                    if self.activo and self.fase_actual == FaseTutorial.OLEADAS:
                        if tipo in clases_enemigos:
                            enemigo = clases_enemigos[tipo](self.juego.camino[0][0], self.juego.camino[0][1])
                            enemigo.ruta = self.juego.camino
                            self.juego.enemigos.append(enemigo)
            except Exception as e:
                print(f"Error en oleada tutorial: {e}")
        
        hilo = threading.Thread(target=generar_oleada)
        hilo.daemon = True
        hilo.start()

    def actualizar(self, dt: float):
        if not self.activo:
            return
        
        self._verificar_objetivos()
        self._logica_fase_especifica(dt)

    def _verificar_objetivos(self):
        tiempo_transcurrido = pygame.time.get_ticks() - self.tiempo_fase_inicio
        
        if self.fase_actual == FaseTutorial.INTERFAZ_BASICA:
            if tiempo_transcurrido > 3000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.COLOCAR_TORRE:
            if len(self.juego.torres) > self.torres_colocadas:
                self.torres_colocadas = len(self.juego.torres)
                self.objetivos_actuales[0].completar()
                
        elif self.fase_actual == FaseTutorial.TIPOS_TORRES:
            if tiempo_transcurrido > 4000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.PRIMER_ENEMIGO:
            enemigos_activos = sum(1 for e in self.juego.enemigos if e.activo)
            if self.enemigos_tutorial_spawneados > 0 and enemigos_activos == 0:
                self.objetivos_actuales[0].completar()
                
        elif self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            if tiempo_transcurrido > 3000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.TIPOS_ENEMIGOS:
            if tiempo_transcurrido > 4000:
                for objetivo in self.objetivos_actuales:
                    objetivo.completar()
                    
        elif self.fase_actual == FaseTutorial.ESTRATEGIA:
            if len(self.juego.torres) >= 3:
                self.objetivos_actuales[2].completar()
            if tiempo_transcurrido > 5000:
                self.objetivos_actuales[0].completar()
                self.objetivos_actuales[1].completar()
                
        elif self.fase_actual == FaseTutorial.OLEADAS:
            if len(self.juego.enemigos) == 0 and tiempo_transcurrido > 5000:
                self.objetivos_actuales[0].completar()

    def _logica_fase_especifica(self, dt: float):
        if self.fase_actual == FaseTutorial.RECURSOS_DINERO:
            dinero_actual = self.juego.gestor_recursos.obtener('dinero')
            self.objetivos_actuales[0].descripcion = f"Dinero actual: ${dinero_actual}"
        
        self.puede_continuar = all(obj.completado for obj in self.objetivos_actuales)

    def manejar_evento(self, evento) -> bool:
        if not self.activo:
            return False
            
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_SPACE:
                if self.puede_continuar or self.fase_actual == FaseTutorial.INICIO:
                    self._avanzar_fase()
                    return True
            elif evento.key == pygame.K_ESCAPE:
                if self.fase_actual == FaseTutorial.VICTORIA:
                    self._salir_tutorial()
                    return True
                    
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.puede_continuar:
                self._avanzar_fase()
                return True
                
        return False

    def _avanzar_fase(self):
        from Main import EstadoJuego
        fases = list(FaseTutorial)
        indice_actual = fases.index(self.fase_actual)
        if indice_actual < len(fases) - 1:
            self.fase_actual = fases[indice_actual + 1]
            self._cargar_fase()
        else:
            self._salir_tutorial()

    def _salir_tutorial(self):
        from Main import EstadoJuego
        self.activo = False
        self.juego.estado_juego = EstadoJuego.MENU

    def dibujar(self, pantalla: pygame.Surface):
        if not self.activo:
            return
        
        # DISEÑO MINIMALISTA - SIN OBSTRUCCIONES
        # Panel principal en esquina superior izquierda, área libre
        panel_x = 10
        panel_y = 160  # Debajo de la info de recursos
        panel_ancho = 400  # Más estrecho
        panel_alto_principal = 60  # Muy compacto
        
        # Panel principal ultra minimalista
        panel_principal = pygame.Rect(panel_x, panel_y, panel_ancho, panel_alto_principal)
        
        # Fondo semi-transparente muy sutil
        s = pygame.Surface((panel_ancho, panel_alto_principal))
        s.set_alpha(220)  # Más transparente
        s.fill(AZUL_CLARO)
        pantalla.blit(s, (panel_x, panel_y))
        
        # Borde muy sutil
        pygame.draw.rect(pantalla, AZUL, panel_principal, 1)
        
        # Título compacto
        titulo = self.fuente_titulo.render(self.mensaje_principal, True, AZUL)
        pantalla.blit(titulo, (panel_x + 8, panel_y + 8))
        
        # Mensaje secundario en una línea
        if self.mensaje_secundario:
            mensaje = self.fuente_texto.render(self.mensaje_secundario, True, GRIS_TEXTO)
            pantalla.blit(mensaje, (panel_x + 8, panel_y + 28))
        
        # Panel de objetivos MUY compacto, en línea horizontal
        objetivos_y = panel_y + panel_alto_principal + 5
        altura_objetivos = 45  # Muy pequeño
        panel_objetivos = pygame.Rect(panel_x, objetivos_y, panel_ancho, altura_objetivos)
        
        # Fondo objetivos semi-transparente
        s2 = pygame.Surface((panel_ancho, altura_objetivos))
        s2.set_alpha(200)
        s2.fill(VERDE_CLARO)
        pantalla.blit(s2, (panel_x, objetivos_y))
        
        pygame.draw.rect(pantalla, VERDE, panel_objetivos, 1)
        
        # Título objetivos pequeño
        titulo_obj = self.fuente_pequeña.render("Objetivos:", True, VERDE)
        pantalla.blit(titulo_obj, (panel_x + 5, objetivos_y + 4))
        
        # Mostrar solo los 2 primeros objetivos para mantenerlo minimalista
        objetivos_mostrar = self.objetivos_actuales[:2]  # Solo primeros 2
        
        y_offset = 18
        for objetivo in objetivos_mostrar:
            color = VERDE if objetivo.completado else GRIS_TEXTO
            simbolo = "✓" if objetivo.completado else "•"
            texto = f"{simbolo} {objetivo.descripcion}"
            
            # Truncar para mantener en una línea
            if len(texto) > 55:
                texto = texto[:52] + "..."
            
            obj_surface = self.fuente_pequeña.render(texto, True, color)
            pantalla.blit(obj_surface, (panel_x + 8, objetivos_y + y_offset))
            y_offset += 12
        
        # Si hay más objetivos, mostrar contador
        if len(self.objetivos_actuales) > 2:
            restantes = len(self.objetivos_actuales) - 2
            contador = self.fuente_pequeña.render(f"(+{restantes} más...)", True, GRIS_TEXTO)
            pantalla.blit(contador, (panel_x + 280, objetivos_y + 30))
        
        # Indicador de continuar minimalista - en la esquina inferior derecha
        if self.puede_continuar:
            continuar_x = 1100
            continuar_y = 750
            continuar_texto = "ESPACIO: Continuar"
            
            # Fondo para el indicador
            continuar_surface = self.fuente_pequeña.render(continuar_texto, True, BLANCO)
            rect_continuar = continuar_surface.get_rect()
            rect_continuar.x = continuar_x
            rect_continuar.y = continuar_y
            
            # Efecto pulsante suave
            pulse = int(50 + 30 * math.sin(pygame.time.get_ticks() * 0.008))
            
            # Fondo pulsante
            fondo_continuar = pygame.Surface((rect_continuar.width + 16, rect_continuar.height + 8))
            fondo_continuar.set_alpha(pulse + 150)
            fondo_continuar.fill(VERDE)
            
            pantalla.blit(fondo_continuar, (continuar_x - 8, continuar_y - 4))
            pygame.draw.rect(pantalla, VERDE, (continuar_x - 8, continuar_y - 4, rect_continuar.width + 16, rect_continuar.height + 8), 2)
            pantalla.blit(continuar_surface, rect_continuar)

    def _dividir_texto(self, texto: str, max_chars: int) -> List[str]:
        """Divide texto en líneas que no excedan el máximo de caracteres"""
        palabras = texto.split()
        lineas = []
        linea_actual = ""
        
        for palabra in palabras:
            if len(linea_actual + " " + palabra) <= max_chars:
                linea_actual += (" " if linea_actual else "") + palabra
            else:
                if linea_actual:
                    lineas.append(linea_actual)
                linea_actual = palabra
        
        if linea_actual:
            lineas.append(linea_actual)
        
        return lineas