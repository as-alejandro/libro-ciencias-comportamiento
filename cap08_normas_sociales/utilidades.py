"""
Funciones comunes a todas las apps del capítulo 8.
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



def leer_repartos(config):
    """
    Convierte el parámetro 'repartos' (texto como '20:80|45:55|80:20') en una lista
    de pares [(20, 80), (45, 55), (80, 20)]: lo que se queda quien reparte y lo que
    recibe la otra persona. Comprueba que el formato sea correcto.
    """
    texto = config['repartos']
    dotacion = config['dotacion']
    try:
        pares = [tuple(int(x) for x in par.split(':')) for par in texto.split('|')]
    except ValueError:
        raise ValueError(
            f'El parámetro "repartos" ("{texto}") no tiene el formato correcto. '
            f'Ejemplo de formato válido: 20:80|45:55|80:20'
        )
    if not 2 <= len(pares) <= 5:
        raise ValueError(f'El parámetro "repartos" debe tener entre 2 y 5 opciones, y tiene {len(pares)}.')
    for par in pares:
        if len(par) != 2 or sum(par) != dotacion:
            raise ValueError(
                f'En el parámetro "repartos", la opción "{":".join(map(str, par))}" '
                f'no suma {dotacion}, que es la dotación.'
            )
    return pares