"""
Funciones comunes a todas las apps del capítulo 9.
"""
import random
import time

# Escenarios de la actividad, en orden. numero_juegos se calcula a partir de esta lista.
ESCENARIOS = [
    'Repartir entre otras dos personas',
    'Repartir entre tú y otra persona',
    'Enviar y devolver',
    'Predicciones',
]
NUMERO_JUEGOS = len(ESCENARIOS)

# Nombre del grupo según el conjunto de pinturas elegido
NOMBRES_GRUPO = dict(A='Klee', B='Kandinsky')

# Máximo de montos que admite 'niveles_confianza' (hay una casilla
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

def otro_grupo(player):
    """Nombre del grupo al que NO pertenece el participante (por ejemplo, 'Kandinsky')."""
    propio = player.participant.grupo_asignado
    return NOMBRES_GRUPO['B'] if propio == NOMBRES_GRUPO['A'] else NOMBRES_GRUPO['A']


def en_orden_aleatorio(player, pregunta, opciones):
    """
    Baraja las opciones de una pregunta de control. Para un mismo participante el
    orden es siempre el mismo, así no cambia cada vez que reintenta.
    """
    azar = random.Random(f'{player.participant.code}-{pregunta}')
    opciones = list(opciones)
    azar.shuffle(opciones)
    return opciones

def leer_niveles(config):
    """
    Convierte el parámetro 'niveles_confianza' (texto como '0|25|50|75|100')
    en una lista ordenada de enteros [0, 25, 50, 75, 100] y comprueba que sea válido.
    """
    texto = config['niveles_confianza']
    dotacion = config['dotacion_confianza']
    try:
        niveles = sorted(int(x) for x in texto.split('|'))
    except ValueError:
        raise ValueError(
            f'El parámetro "niveles_confianza" ("{texto}") no tiene el formato correcto. '
            f'Ejemplo de formato válido: 0|25|50|75|100'
        )
    if not 2 <= len(niveles) <= MAX_NIVELES:
        raise ValueError(
            f'"niveles_confianza" tiene que tener entre 2 y {MAX_NIVELES} montos, '
            f'y tiene {len(niveles)}.'
        )
    if len(set(niveles)) != len(niveles):
        raise ValueError('En "niveles_confianza" hay montos repetidos.')
    if niveles[0] < 0:
        raise ValueError('En "niveles_confianza" no puede haber montos negativos.')
    if niveles[-1] != dotacion:
        raise ValueError(
            f'El monto más alto de "niveles_confianza" ({niveles[-1]}) tiene que ser igual a '
            f'"dotacion_confianza" ({dotacion}).'
        )
    referencia = config['nivel_referencia_creencias']
    if referencia not in niveles or referencia == 0:
        raise ValueError(
            f'"nivel_referencia_creencias" ({referencia}) tiene que ser uno de los montos de '
            f'"niveles_confianza" ({texto}) y no puede ser 0.'
        )
    return niveles

def error_entero(valor, minimo, maximo, vacio):
    """
    Revisión en el servidor de un campo entero: el mensaje de error, o None si está bien.
    (Los decimales y el texto los detiene antes la plantilla validar_numeros.html.)
    """
    if valor is None:
        return vacio
    if not minimo <= valor <= maximo:
        return f'El valor debe estar entre {minimo} y {maximo}.'
    return None


def rango(minimo, maximo, vacio):
    """Datos de un campo para validar_numeros.html."""
    return dict(min=minimo, max=maximo, vacio=vacio)

def lista_en_palabras(numeros):
    """[0, 25, 50, 75, 100] -> '0, 25, 50, 75 o 100'."""
    textos = [str(n) for n in numeros]
    return ', '.join(textos[:-1]) + ' o ' + textos[-1]