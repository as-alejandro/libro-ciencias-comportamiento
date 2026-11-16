"""
Funciones comunes a todas las apps del capítulo 9.
"""
import time


# Máximo de montos que admite 'niveles_enviado_confianza' (hay una casilla
# preparada por monto y por grupo en la pantalla del receptor)
MAX_NIVELES = 11

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


def leer_niveles(config):
    """
    Convierte el parámetro 'niveles_enviado_confianza' (texto como '0|25|50|75|100')
    en una lista de enteros [0, 25, 50, 75, 100] y comprueba que sea válido.
    """
    texto = config['niveles_enviado_confianza']
    dotacion = config['dotacion_confianza']
    try:
        niveles = [int(x) for x in texto.split('|')]
    except ValueError:
        raise ValueError(
            f'El parámetro "niveles_enviado_confianza" ("{texto}") no tiene el formato correcto. '
            f'Ejemplo de formato válido: 0|25|50|75|100'
        )
    if not 1 <= len(niveles) <= MAX_NIVELES:
        raise ValueError(
            f'"niveles_enviado_confianza" tiene que tener entre 1 y {MAX_NIVELES} montos, '
            f'y tiene {len(niveles)}.'
        )
    if len(set(niveles)) != len(niveles):
        raise ValueError('En "niveles_enviado_confianza" hay montos repetidos.')
    for nivel in niveles:
        if not 0 <= nivel <= dotacion:
            raise ValueError(
                f'En "niveles_enviado_confianza", el monto {nivel} tiene que estar '
                f'entre 0 y {dotacion}, que es la dotación de la confianza.'
            )
    if config['nivel_referencia_creencias'] not in niveles:
        raise ValueError(
            f'"nivel_referencia_creencias" ({config["nivel_referencia_creencias"]}) tiene que ser '
            f'uno de los montos de "niveles_enviado_confianza" ({texto}).'
        )
    return niveles