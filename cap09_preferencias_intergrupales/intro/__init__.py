from otree.api import *
from datetime import datetime
from utilidades import leer_niveles, iniciar_cronometro, segundos_transcurridos
import random
import itertools


doc = """
Capítulo 9. Preferencias intergrupales. App 1: introducción.
Consentimiento, categorización, instrucciones generales y control de comprensión 1.
"""


class C(BaseConstants):
    NAME_IN_URL = 'intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


VALORES_VALIDOS = dict(
    incentivos=['hipotetico', 'puntos', 'dinero_real'],
    modo_pago=['una_decision_propia', 'prob_pago_subconjunto'],
    metodo_induccion_grupo=['pinturas', 'colores', 'moneda'],
    orden_contraparte_dictador=['propio_primero', 'otro_primero', 'aleatorio'],
    orden_bloques_confianza=['emisor_primero', 'receptor_primero', 'aleatorio'],
    orden_grupo_confianza=['propio_primero', 'otro_primero', 'aleatorio'],
    orden_grupo_creencias=['propio_primero', 'otro_primero', 'aleatorio'],
)

# Los cuatro órdenes que se asignan a cada participante, con sus dos valores posibles
ORDENES = dict(
    orden_contraparte_dictador=['propio_primero', 'otro_primero'],
    orden_bloques_confianza=['emisor_primero', 'receptor_primero'],
    orden_grupo_confianza=['propio_primero', 'otro_primero'],
    orden_grupo_creencias=['propio_primero', 'otro_primero'],
)


def comprobar_parametros(config):
    """Detiene la creación de la sesión si algún parámetro no es válido."""
    for parametro, validos in VALORES_VALIDOS.items():
        if config[parametro] not in validos:
            raise ValueError(
                f'El parámetro "{parametro}" tiene el valor "{config[parametro]}", '
                f'que no es válido. Valores posibles: {", ".join(validos)}.'
            )
    if config['incentivos'] == 'dinero_real' and config['tasa_cambio'] <= 0:
        raise ValueError(
            'Con incentivos = dinero_real hay que fijar "tasa_cambio" (pesos por ficha) '
            'antes de abrir la sesión.'
        )
    if config['prob_pago'] < 1:
        raise ValueError('"prob_pago" tiene que ser 1 o más.')
    if config['multiplicador_confianza'] < 1:
        raise ValueError('"multiplicador_confianza" tiene que ser 1 o más.')
    if config['categorias_likert_identificacion'] not in [5, 7]:
        raise ValueError('"categorias_likert_identificacion" tiene que ser 5 o 7.')
    leer_niveles(config)


def creating_session(subsession: Subsession):
    """Comprueba los parámetros y asigna a cada participante sus cuatro órdenes."""
    config = subsession.session.config
    comprobar_parametros(config)
    semilla = config['semilla']
    azar = random.Random(semilla) if semilla else random.Random()

    # Para cada orden: si el parámetro es 'aleatorio' entran los dos valores; si no, solo el elegido
    posibles = [
        valores if config[nombre] == 'aleatorio' else [config[nombre]]
        for nombre, valores in ORDENES.items()
    ]
    combinaciones = list(itertools.product(*posibles))

    # Bloques equilibrados: se reparte una combinación de cada tipo, barajadas,
    # y se repite hasta cubrir a todos los participantes
    jugadores = subsession.get_players()
    asignaciones = []
    while len(asignaciones) < len(jugadores):
        bloque = combinaciones.copy()
        azar.shuffle(bloque)
        asignaciones.extend(bloque)

    for jugador, combinacion in zip(jugadores, asignaciones):
        for nombre, valor in zip(ORDENES, combinacion):
            jugador.participant.vars[nombre] = valor
            setattr(jugador, nombre, valor)

    # Con el método 'moneda', el grupo se sortea aquí: mitad A y mitad B
    if config['metodo_induccion_grupo'] == 'moneda':
        grupos = ['A', 'B'] * (len(jugadores) // 2 + 1)
        grupos = grupos[:len(jugadores)]
        azar.shuffle(grupos)
        for jugador, grupo in zip(jugadores, grupos):
            jugador.participant.vars['grupo_sorteado'] = grupo


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
    categorizacion_eleccion = models.StringField(label='', widget=widgets.RadioSelect)
    categorizacion_segundos = models.IntegerField(blank=True)
    grupo_asignado = models.StringField(blank=True)
    segundos_instrucciones = models.IntegerField(blank=True)
    control1_p1 = models.IntegerField(
        label='¿Cuándo podrás ver lo que han respondido los demás participantes?',
        choices=[
            [1, 'Antes de tomar mis decisiones'],
            [2, 'Solo cuando termine la actividad'],
            [3, 'En ningún momento'],
        ],
        widget=widgets.RadioSelect,
    )
    control1_p2 = models.IntegerField(
        label='¿Cómo se calcula lo que ganas en esta actividad?',
        choices=[
            [1, 'Se suman las ganancias de todas mis decisiones'],
            [2, 'Se sortea una de mis decisiones y gano lo que obtuve en ella'],
            [3, 'Gano lo mismo que el resto de mi grupo'],
        ],
        widget=widgets.RadioSelect,
    )
    control1_intentos = models.IntegerField(initial=0)
    # Copia de los órdenes asignados, para verlos en la pestaña Data
    orden_contraparte_dictador = models.StringField()
    orden_bloques_confianza = models.StringField()
    orden_grupo_confianza = models.StringField()
    orden_grupo_creencias = models.StringField()


# PÁGINAS

class Consentimiento(Page):
    form_model = 'player'
    form_fields = ['consentimiento']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.consentimiento = player.consentimiento
        if player.consentimiento:
            player.hora_inicio = datetime.now().isoformat(timespec='seconds')

# FUNCIONES

# Opciones de la categorización y el grupo al que lleva cada una (A o B)
OPCIONES_CATEGORIZACION = dict(
    pinturas=[['A', 'Conjunto A'], ['B', 'Conjunto B']],
    colores=[['azul', 'Azul'], ['verde', 'Verde']],
)
GRUPO_DE_LA_ELECCION = dict(A='A', B='B', azul='A', verde='B')


def categorizacion_eleccion_choices(player: Player):
    return OPCIONES_CATEGORIZACION[player.session.config['metodo_induccion_grupo']]

class Categorizacion(Page):
    form_model = 'player'

    @staticmethod
    def is_displayed(player: Player):
        return player.consentimiento

    @staticmethod
    def get_form_fields(player: Player):
        # Con 'moneda' no hay nada que elegir: solo se lee y se avanza
        if player.session.config['metodo_induccion_grupo'] == 'moneda':
            return []
        return ['categorizacion_eleccion']

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'categorizacion')
        return dict(metodo=player.session.config['metodo_induccion_grupo'])

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.categorizacion_segundos = segundos_transcurridos(player, 'categorizacion')
        if player.session.config['metodo_induccion_grupo'] == 'moneda':
            grupo = player.participant.vars['grupo_sorteado']
        else:
            grupo = GRUPO_DE_LA_ELECCION[player.categorizacion_eleccion]
        player.grupo_asignado = grupo
        player.participant.grupo_asignado = grupo


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


# Respuesta correcta de cada pregunta del control 1
CORRECTAS_CONTROL1 = dict(control1_p1=2, control1_p2=2)


class Control1(Page):
    form_model = 'player'

    @staticmethod
    def is_displayed(player: Player):
        return player.consentimiento

    @staticmethod
    def get_form_fields(player: Player):
        # En modo hipotético no hay ganancias, así que no se pregunta por ellas
        if player.session.config['incentivos'] == 'hipotetico':
            return ['control1_p1']
        return ['control1_p1', 'control1_p2']

    @staticmethod
    def error_message(player: Player, values):
        player.control1_intentos += 1
        if not player.session.config['exigir_controles']:
            return None
        errores = {}
        for campo, respuesta in values.items():
            if respuesta != CORRECTAS_CONTROL1[campo]:
                errores[campo] = 'Esta respuesta no es correcta. Vuelve a intentarlo.'
        return errores


page_sequence = [Consentimiento, Categorizacion, Instrucciones, Control1]