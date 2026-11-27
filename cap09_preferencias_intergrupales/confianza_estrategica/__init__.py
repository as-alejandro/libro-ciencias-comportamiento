from otree.api import *
from utilidades import (iniciar_cronometro, segundos_transcurridos, leer_niveles,
                        lista_en_palabras, en_orden_aleatorio, error_entero, rango)

doc = """
Capítulo 9. Preferencias intergrupales. App 4: juego de confianza, método de la estrategia.
Escenario 3: Enviar y devolver. Introducción con control 3 y cuatro pantallas de decisión:
dos como quien envía y dos como quien recibe (una por grupo de la otra persona).
El orden de los roles sale de orden_bloques_confianza y el de los grupos, de
orden_grupo_confianza.
"""


class C(BaseConstants):
    NAME_IN_URL = 'confianza_estrategica'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def devolucion():
    """Casilla del receptor: cuánto devuelve en un caso concreto."""
    return models.IntegerField(label='', min=None, blank=True)

def envio():
    """Botones del emisor. blank=True para mostrar nuestro propio mensaje si no elige."""
    return models.IntegerField(label='', widget=widgets.RadioSelectHorizontal, blank=True)


class Player(BasePlayer):
    control3 = models.IntegerField(
        label='En las dos pantallas siguientes, ¿para qué casos tienes que responder?',
        widget=widgets.RadioSelect,
    )
    control3_intentos = models.IntegerField(initial=0)
    conf_emisor_propio = envio()
    conf_emisor_otro = envio()
    conf_emisor_propio_segundos = models.IntegerField(blank=True)
    conf_emisor_otro_segundos = models.IntegerField(blank=True)
    conf_receptor_propio_1 = devolucion()
    conf_receptor_propio_2 = devolucion()
    conf_receptor_propio_3 = devolucion()
    conf_receptor_propio_4 = devolucion()
    conf_receptor_propio_5 = devolucion()
    conf_receptor_propio_6 = devolucion()
    conf_receptor_propio_7 = devolucion()
    conf_receptor_propio_8 = devolucion()
    conf_receptor_propio_9 = devolucion()
    conf_receptor_propio_10 = devolucion()
    conf_receptor_propio_11 = devolucion()
    conf_receptor_otro_1 = devolucion()
    conf_receptor_otro_2 = devolucion()
    conf_receptor_otro_3 = devolucion()
    conf_receptor_otro_4 = devolucion()
    conf_receptor_otro_5 = devolucion()
    conf_receptor_otro_6 = devolucion()
    conf_receptor_otro_7 = devolucion()
    conf_receptor_otro_8 = devolucion()
    conf_receptor_otro_9 = devolucion()
    conf_receptor_otro_10 = devolucion()
    conf_receptor_otro_11 = devolucion()
    conf_receptor_propio_segundos = models.IntegerField(blank=True)
    conf_receptor_otro_segundos = models.IntegerField(blank=True)


# FUNCIONES

def participa(player: Player):
    return player.participant.consentimiento


def control3_choices(player: Player):
    return en_orden_aleatorio(player, 'control3', [
        [1, 'Solo para el caso que me vaya a tocar'],
        [2, 'Para todos los casos posibles, aunque al final solo se use uno de ellos'],
        [3, 'Solo para los casos en que la otra persona es de mi propio grupo'],
    ])


def opciones_envio(player: Player):
    """Los montos de niveles_confianza, de menor a mayor: [[0, '0'], [25, '25'], ...]."""
    return [[nivel, str(nivel)] for nivel in leer_niveles(player.session.config)]


def conf_emisor_propio_choices(player: Player):
    return opciones_envio(player)


def conf_emisor_otro_choices(player: Player):
    return opciones_envio(player)


def grupos_en_orden(player: Player):
    if player.participant.orden_grupo_confianza == 'propio_primero':
        return ['propio', 'otro']
    return ['otro', 'propio']


def roles_en_orden(player: Player):
    if player.participant.orden_bloques_confianza == 'emisor_primero':
        return ['emisor', 'receptor']
    return ['receptor', 'emisor']


def pantalla(player: Player, k):
    """
    Qué toca en la pantalla de decisión número k (1 a 4): el rol, el grupo de la otra
    persona y si es la 1 o la 2 de ese rol. Ejemplo: ('receptor', 'otro', 1).
    """
    rol = roles_en_orden(player)[(k - 1) // 2]
    numero = 1 if k % 2 == 1 else 2
    grupo = grupos_en_orden(player)[numero - 1]
    return rol, grupo, numero


def filas_receptor(player: Player, grupo):
    """Una fila por monto que se puede recibir. La fila de 0 enviadas no se pregunta."""
    config = player.session.config
    filas = []
    for i, nivel in enumerate(leer_niveles(config), start=1):
        if nivel == 0:
            continue
        filas.append(dict(
            enviado=nivel,
            recibido=nivel * config['multiplicador_confianza'],
            campo=f'conf_receptor_{grupo}_{i}',
        ))
    return filas


def campos(player: Player, k):
    rol, grupo, numero = pantalla(player, k)
    if rol == 'emisor':
        return [f'conf_emisor_{grupo}']
    return [fila['campo'] for fila in filas_receptor(player, grupo)]


def datos_pantalla(player: Player, k):
    rol, grupo, numero = pantalla(player, k)
    iniciar_cronometro(player, f'conf_{rol}_{grupo}')
    return dict(
        es_emisor=rol == 'emisor',
        es_propio=grupo == 'propio',
        numero=numero,
        filas=filas_receptor(player, grupo),
        # Límites de cada casilla del receptor (el emisor usa botones y no necesita)
        rangos={} if rol == 'emisor' else {
            fila['campo']: rango(0, fila['recibido'], 'Completa este campo.')
            for fila in filas_receptor(player, grupo)
        },
    )

def errores_pantalla(player: Player, values, k):
    rol, grupo, numero = pantalla(player, k)
    errores = {}
    if rol == 'emisor':
        if values[f'conf_emisor_{grupo}'] is None:
            errores[f'conf_emisor_{grupo}'] = 'Elige una de las opciones.'
        return errores
    for fila in filas_receptor(player, grupo):
        error = error_entero(values[fila['campo']], 0, fila['recibido'], 'Completa este campo.')
        if error:
            errores[fila['campo']] = error
    return errores

def guardar_tiempo(player: Player, k):
    rol, grupo, numero = pantalla(player, k)
    setattr(player, f'conf_{rol}_{grupo}_segundos',
            segundos_transcurridos(player, f'conf_{rol}_{grupo}'))


# PÁGINAS

class Control3(Page):
    form_model = 'player'
    form_fields = ['control3']

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def vars_for_template(player: Player):
        config = player.session.config
        return dict(
            niveles=lista_en_palabras(leer_niveles(config)),
            maximo_recibido=config['dotacion_confianza'] * config['multiplicador_confianza'],
        )

    @staticmethod
    def error_message(player: Player, values):
        player.control3_intentos += 1
        if not player.session.config['exigir_controles']:
            return None
        if values['control3'] != 2:
            return dict(control3='Esta respuesta no es correcta. Vuelve a intentarlo.')


class Decision(Page):
    """Base de las cuatro pantallas de decisión. Cada una solo cambia su número k."""
    form_model = 'player'
    template_name = 'confianza_estrategica/Decision.html'

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)


class Decision1(Decision):
    @staticmethod
    def get_form_fields(player: Player):
        return campos(player, 1)

    @staticmethod
    def vars_for_template(player: Player):
        return datos_pantalla(player, 1)

    @staticmethod
    def error_message(player: Player, values):
        return errores_pantalla(player, values, 1)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        guardar_tiempo(player, 1)


class Decision2(Decision):
    @staticmethod
    def get_form_fields(player: Player):
        return campos(player, 2)

    @staticmethod
    def vars_for_template(player: Player):
        return datos_pantalla(player, 2)

    @staticmethod
    def error_message(player: Player, values):
        return errores_pantalla(player, values, 2)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        guardar_tiempo(player, 2)


class Decision3(Decision):
    @staticmethod
    def get_form_fields(player: Player):
        return campos(player, 3)

    @staticmethod
    def vars_for_template(player: Player):
        return datos_pantalla(player, 3)

    @staticmethod
    def error_message(player: Player, values):
        return errores_pantalla(player, values, 3)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        guardar_tiempo(player, 3)


class Decision4(Decision):
    @staticmethod
    def get_form_fields(player: Player):
        return campos(player, 4)

    @staticmethod
    def vars_for_template(player: Player):
        return datos_pantalla(player, 4)

    @staticmethod
    def error_message(player: Player, values):
        return errores_pantalla(player, values, 4)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        guardar_tiempo(player, 4)


page_sequence = [Control3, Decision1, Decision2, Decision3, Decision4]