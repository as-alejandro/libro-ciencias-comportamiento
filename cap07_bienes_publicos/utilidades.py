"""
Funciones comunes a todas las apps del capítulo 7.
"""
import time


def iniciar_cronometro(player, nombre):
    """Guarda el momento en que el participante abre una pantalla."""
    clave = 'inicio_' + nombre
    if clave not in player.participant.vars:
        player.participant.vars[clave] = time.time()


def segundos_transcurridos(player, nombre):
    """Devuelve los segundos que pasaron desde que se abrió la pantalla."""
    inicio = player.participant.vars.get('inicio_' + nombre)
    if inicio is None:
        return None
    return round(time.time() - inicio)