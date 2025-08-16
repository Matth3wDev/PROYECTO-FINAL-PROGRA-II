import pygame
import logging
import traceback
from datetime import datetime
from typing import Optional, Any


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('defense_zone_errors.log'),
        logging.StreamHandler()
    ]
)

class Excepcion_juego(Exception):  
    def __init__(self, mensaje: str, codigo_error: Optional[str] = None, 
                 contexto: Optional[dict] = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_error = codigo_error or self.__class__.__name__
        self.contexto = contexto or {}
        self.marca_tiempo = datetime.now()
        self._registrar_error()
    
    def _registrar_error(self):
        logger = logging.getLogger(self.__class__.__name__)
        info_error = {
            'codigo_error': self.codigo_error,
            'mensaje': self.mensaje,
            'marca_tiempo': self.marca_tiempo.isoformat(),
            'contexto': self.contexto
        }
        logger.error(f"Excepción del Juego: {info_error}")
    
    def obtener_detalles_error(self) -> dict:
        return {
            'tipo': self.__class__.__name__,
            'mensaje': self.mensaje,
            'codigo_error': self.codigo_error,
            'marca_tiempo': self.marca_tiempo.isoformat(),
            'contexto': self.contexto,
            'traceback': traceback.format_exc()
        }
    
    def __str__(self) -> str:
        if self.codigo_error:
            return f"[{self.codigo_error}] {self.mensaje}"
        return self.mensaje

class ExcepcionColocacionTorre(Excepcion_juego):
    """
    Excepción para errores de colocación de torres.
    """
    def __init__(self, mensaje: str, posicion: tuple = None, 
                 tipo_torre: str = None, razon: str = None):
        contexto = {
            'posicion': posicion,
            'tipo_torre': tipo_torre,
            'razon': razon
        }
        super().__init__(
            mensaje, 
            codigo_error="COLOCACION_TORRE_001", 
            contexto=contexto
        )
        self.posicion = posicion
        self.tipo_torre = tipo_torre
        self.razon = razon
    
    @classmethod
    def muy_cerca_del_camino(cls, posicion: tuple, tipo_torre: str):
        return cls(
            f"No se puede colocar {tipo_torre} en {posicion}: demasiado cerca del camino",
            posicion=posicion,
            tipo_torre=tipo_torre,
            razon="muy_cerca_del_camino"
        )
    
    @classmethod
    def muy_cerca_de_otra_torre(cls, posicion: tuple, tipo_torre: str, posicion_torre_existente: tuple):
        return cls(
            f"No se puede colocar {tipo_torre} en {posicion}: demasiado cerca de otra torre en {posicion_torre_existente}",
            posicion=posicion,
            tipo_torre=tipo_torre,
            razon="muy_cerca_de_otra_torre"
        )

class ExcepcionRecursosInsuficientes(Excepcion_juego):
    """
    Excepción para errores de recursos insuficientes.
    """
    def __init__(self, mensaje: str, cantidad_requerida: int = None, 
                 cantidad_disponible: int = None, tipo_recurso: str = None):
        contexto = {
            'cantidad_requerida': cantidad_requerida,
            'cantidad_disponible': cantidad_disponible,
            'tipo_recurso': tipo_recurso,
            'deficit': cantidad_requerida - cantidad_disponible if (cantidad_requerida and cantidad_disponible) else None
        }
        super().__init__(
            mensaje,
            codigo_error="RECURSOS_INSUFICIENTES_001",
            contexto=contexto
        )
        self.cantidad_requerida = cantidad_requerida
        self.cantidad_disponible = cantidad_disponible
        self.tipo_recurso = tipo_recurso
    
    @classmethod
    def dinero_insuficiente(cls, costo: int, disponible: int, nombre_item: str = "ítem"):
        return cls(
            f"No tienes suficiente dinero para {nombre_item}. Requerido: {costo}, disponible: {disponible}",
            cantidad_requerida=costo,
            cantidad_disponible=disponible,
            tipo_recurso="dinero"
        )
    
    def obtener_faltante(self) -> int:
        if self.cantidad_requerida and self.cantidad_disponible:
            return self.cantidad_requerida - self.cantidad_disponible
        return 0

class ExcepcionConfiguracionOleadaInvalida(Excepcion_juego):
    """
    Excepción para errores en la configuración de oleadas.
    """
    def __init__(self, mensaje: str, numero_oleada: int = None, 
                 configuracion: dict = None):
        contexto = {
            'numero_oleada': numero_oleada,
            'configuracion': configuracion
        }
        super().__init__(
            mensaje,
            codigo_error="OLEADA_INVALIDA_001",
            contexto=contexto
        )
        self.numero_oleada = numero_oleada
        self.configuracion = configuracion

class ExcepcionEstadoJuego(Excepcion_juego):
    """
    Excepción para errores de estado del juego.
    """
    def __init__(self, mensaje: str, estado_actual: str = None, 
                 estado_requerido: str = None, operacion: str = None):
        contexto = {
            'estado_actual': estado_actual,
            'estado_requerido': estado_requerido,
            'operacion': operacion
        }
        super().__init__(
            mensaje,
            codigo_error="ESTADO_JUEGO_INVALIDO_001",
            contexto=contexto
        )
        self.estado_actual = estado_actual
        self.estado_requerido = estado_requerido
        self.operacion = operacion


class ExcepcionGeneracionEnemigo(Excepcion_juego):
    """
    Excepción para errores de generación de enemigos.
    """
    def __init__(self, mensaje: str, tipo_enemigo: str = None, 
                 posicion_generacion: tuple = None):
        contexto = {
            'tipo_enemigo': tipo_enemigo,
            'posicion_generacion': posicion_generacion
        }
        super().__init__(
            mensaje,
            codigo_error="GENERACION_ENEMIGOS_001",
            contexto=contexto
        )
        self.tipo_enemigo = tipo_enemigo
        self.posicion_generacion = posicion_generacion


class ExcepcionGeneracionEnemigos(ExcepcionGeneracionEnemigo):
    """
    Alias para mantener compatibilidad hacia atrás.
    """
    pass

class ExcepcionGuardarCargar(Excepcion_juego):
    """
    Excepción para errores de guardado/carga del juego.
    """
    def __init__(self, mensaje: str, operacion: str = None, 
                 ruta_archivo: str = None, datos: Any = None):
        contexto = {
            'operacion': operacion,
            'ruta_archivo': ruta_archivo,
            'tipo_datos': type(datos).__name__ if datos else None
        }
        super().__init__(
            mensaje,
            codigo_error="GUARDAR_CARGAR_001",
            contexto=contexto
        )
        self.operacion = operacion
        self.ruta_archivo = ruta_archivo
        self.datos = datos


def manejar_excepciones_juego(func):
    """
    Decorador para manejo automático de excepciones del juego.
    """
    def envoltura(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Excepcion_juego as e:
            print(f"Excepción del juego capturada: {e}")
        except Exception as e:
            print(f"Excepción inesperada: {e}")
    return envoltura


def resumen_excepciones():
    """Generar un resumen de todas las excepciones registradas"""
    try:
        with open('defense_zone_errors.log', 'r') as f:
            print(f.read())
    except FileNotFoundError:
        print("No se encontró archivo de log de errores")

def limpiar_log_errores():
    """Limpiar el archivo de log de errores"""
    try:
        with open('defense_zone_errors.log', 'w') as f:
            pass
        print("Log de errores limpiado exitosamente")
    except Exception as e:
        print(f"Error al limpiar log: {e}")


if __name__ == "__main__":
    print("Probando Excepciones del Juego...")

    
    try:
        raise Excepcion_juego("Error de prueba", codigo_error="PRUEBA_001")
    except Excepcion_juego as e:
        print(f"Capturada: {e}")
        print(f"Detalles: {e.obtener_detalles_error()}")

    
    try:
        raise ExcepcionColocacionTorre.muy_cerca_del_camino((100, 200), "cañón")
    except ExcepcionColocacionTorre as e:
        print(f"Error de colocación de torre: {e}")

    
    try:
        raise ExcepcionRecursosInsuficientes.dinero_insuficiente(100, 50, "Torre Cañón")
    except ExcepcionRecursosInsuficientes as e:
        print(f"Error de recursos: {e}")
        print(f"Faltante: ${e.obtener_faltante()}")

    
    try:
        raise ExcepcionGeneracionEnemigo("Error de prueba enemigo", "basico", (100, 100))
    except ExcepcionGeneracionEnemigo as e:
        print(f"Error de generación enemigo: {e}")

    
    @manejar_excepciones_juego
    def funcion_prueba():
        raise Excepcion_juego("Error decorador")

    funcion_prueba()

    
    resumen_excepciones()

    print("Pruebas de excepciones completadas!")