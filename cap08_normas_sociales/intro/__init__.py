from otree.api import *
from datetime import datetime
from utilidades import iniciar_cronometro, segundos_transcurridos, leer_repartos
import random
import itertools


doc = """
Capítulo 8. Normas sociales. App 1: introducción.
Consentimiento, instrucciones generales y control de comprensión.
"""


class C(BaseConstants):
    NAME_IN_URL = 'intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass
def opciones(valor, posibles):
    """Si el parámetro es 'aleatorio', devuelve todas las opciones; si no, solo la elegida."""
    if valor == 'aleatorio':
        return posibles
    return [valor]

VALORES_VALIDOS = dict(
    incentivos=['hipotetico', 'puntos', 'monetario'],
    marco=['ganada', 'asignada', 'aleatorio'],
    metodo=['bx', 'kw', 'ambos', 'aleatorio'],
    orden_metodo=['bx_kw', 'kw_bx', 'aleatorio'],
    orden_bloques=['norma_primero', 'decision_primero', 'aleatorio'],
    tarea_esfuerzo=['cuestionario'],  # 'conteo' y 'ninguna': pendientes de definir con la autora
)


def comprobar_parametros(config):
    """Detiene la creación de la sesión si algún parámetro tiene un valor no válido."""
    for parametro, validos in VALORES_VALIDOS.items():
        if config[parametro] not in validos:
            raise ValueError(
                f'El parámetro "{parametro}" tiene el valor "{config[parametro]}", '
                f'que no es válido. Valores posibles: {", ".join(validos)}.'
            )

def creating_session(subsession: Subsession):
    """Asigna a cada participante su condición experimental (asignación silenciosa)."""
    config = subsession.session.config
    comprobar_parametros(config)
    leer_repartos(config)
    if config['categorias_kw'] not in [4, 5, 6]:
        raise ValueError('El parámetro "categorias_kw" debe ser 4, 5 o 6.')
    semilla = config['semilla']
    azar = random.Random(semilla) if semilla else random.Random()

    marcos = opciones(config['marco'], ['ganada', 'asignada'])
    metodos = opciones(config['metodo'], ['bx', 'kw'])
    ordenes_bloques = opciones(config['orden_bloques'], ['norma_primero', 'decision_primero'])
    if config['metodo'] == 'ambos':
        ordenes_metodo = opciones(config['orden_metodo'], ['bx_kw', 'kw_bx'])
    else:
        ordenes_metodo = ['']

    # Todas las combinaciones posibles de condiciones
    combinaciones = list(itertools.product(marcos, metodos, ordenes_metodo, ordenes_bloques))

    # Bloques equilibrados: se reparte una combinación de cada tipo, en orden
    # aleatorio, y se repite hasta cubrir a todos los participantes.
    jugadores = subsession.get_players()
    asignaciones = []
    while len(asignaciones) < len(jugadores):
        bloque = combinaciones.copy()
        azar.shuffle(bloque)
        asignaciones.extend(bloque)

    for jugador, combinacion in zip(jugadores, asignaciones):
        marco, metodo, orden_metodo, orden_bloques = combinacion
        participante = jugador.participant
        participante.marco = jugador.marco = marco
        participante.metodo = jugador.metodo = metodo
        participante.orden_metodo = jugador.orden_metodo = orden_metodo
        participante.orden_bloques = jugador.orden_bloques = orden_bloques


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    consentimiento = models.BooleanField(
        label='',
        choices=[
            [True, 'Acepto participar'],
            [False, 'No acepto participar'],
        ],
        widget=widgets.RadioSelect,
    )
    hora_inicio = models.StringField(blank=True)
    # Copia de las condiciones asignadas, para verlas en la pestaña Data
    marco = models.StringField()
    metodo = models.StringField()
    orden_metodo = models.StringField(blank=True)
    orden_bloques = models.StringField()
    segundos_instrucciones = models.IntegerField(blank=True)

    control1_p1 = models.IntegerField(
        label='¿Cuándo podrás ver lo que han respondido los demás participantes?',
        choices=[
            [1, 'Antes de tomar mi decisión'],
            [2, 'Solo cuando termine la actividad'],
            [3, 'En ningún momento'],
        ],
        widget=widgets.RadioSelect,
    )
    control1_p2 = models.IntegerField(
        label='Cuando te preguntemos qué debería hacer otra persona en una situación, '
              '¿qué tienes que responder?',
        choices=[
            [1, 'Lo que creo que esa persona va a hacer'],
            [2, 'Lo que yo haría si estuviera en su lugar'],
            [3, 'Lo que creo que se debería hacer en esa situación'],
        ],
        widget=widgets.RadioSelect,
    )
    control1_intentos = models.IntegerField(initial=0)

# FUNCIONES

# PÁGINAS

class Consentimiento(Page):
    form_model = 'player'
    form_fields = ['consentimiento']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.consentimiento = player.consentimiento
        if player.consentimiento:
            player.hora_inicio = datetime.now().isoformat(timespec='seconds')


class NoAcepta(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not player.consentimiento


class Instrucciones(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.consentimiento

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'instrucciones')
        return dict()

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.segundos_instrucciones = segundos_transcurridos(player, 'instrucciones')


class Control1(Page):
    form_model = 'player'
    form_fields = ['control1_p1', 'control1_p2']

    @staticmethod
    def is_displayed(player: Player):
        return player.consentimiento

    @staticmethod
    def error_message(player: Player, values):
        player.control1_intentos += 1
        if not player.session.config['exigir_controles']:
            return None
        errores = {}
        if values['control1_p1'] != 2:
            errores['control1_p1'] = 'Esta respuesta no es correcta. Vuelve a intentarlo.'
        if values['control1_p2'] != 3:
            errores['control1_p2'] = 'Esta respuesta no es correcta. Vuelve a intentarlo.'
        return errores


page_sequence = [Consentimiento, Instrucciones, Control1]