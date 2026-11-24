from otree.api import *
import math
import random


doc = """
Capítulo de aversión al riesgo. Lista de precios múltiple de Holt y Laury (2002).
Una sola app: consentimiento, instrucciones, práctica, las 10 decisiones y el pago.
"""


class C(BaseConstants):
    NAME_IN_URL = 'loterias'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    NUM_DECISIONES = 10
    PASO_PROB = 10    # probabilidad del pago alto en la decisión k = PASO_PROB × k (%)
    SORTEO_MAX = 100  # los números aleatorios van de 1 a SORTEO_MAX


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    """Detiene la creación de la sesión si los pagos de las loterías no tienen sentido."""
    c = subsession.session.config
    if not (c['a_alto'] > c['a_bajo'] > 0 and c['b_alto'] > c['b_bajo'] > 0):
        raise ValueError(
            'Los pagos tienen que cumplir a_alto > a_bajo > 0 y b_alto > b_bajo > 0 '
            '(con pagos de 0 no se puede calcular el coeficiente CRRA).'
        )
    if not (c['b_alto'] > c['a_alto'] and c['a_bajo'] > c['b_bajo']):
        raise ValueError(
            'La opción B tiene que ser la arriesgada: b_alto > a_alto y a_bajo > b_bajo.'
        )
    if not 0 <= c['pract_prob'] <= 100:
        raise ValueError('"pract_prob" es un porcentaje: tiene que estar entre 0 y 100.')


class Group(BaseGroup):
    pass

def opcion_ab():
    """Casilla de una decisión de la lista: 'A' o 'B'."""
    return models.StringField(choices=['A', 'B'])

class Player(BasePlayer):
    # Pantalla 1
    consentimiento = models.BooleanField(
        label='He leído esta información y acepto participar.',
        widget=widgets.CheckboxInput,
        blank=True,
    )

    # Pantalla 3: práctica
    practica_eleccion = models.StringField(choices=['X', 'Y'])
    practica_numero = models.IntegerField(blank=True)
    practica_pago = models.IntegerField(blank=True)

    
    # Pantalla 4: las 10 decisiones
    opcion_1 = opcion_ab()
    opcion_2 = opcion_ab()
    opcion_3 = opcion_ab()
    opcion_4 = opcion_ab()
    opcion_5 = opcion_ab()
    opcion_6 = opcion_ab()
    opcion_7 = opcion_ab()
    opcion_8 = opcion_ab()
    opcion_9 = opcion_ab()
    opcion_10 = opcion_ab()

    # Variables derivadas (se calculan al validar la pantalla 4)
    num_seguras = models.IntegerField(blank=True)
    fila_cambio = models.IntegerField(blank=True)
    direccion_cambio = models.StringField(blank=True)
    num_cambios = models.IntegerField(blank=True)
    elige_dominada = models.BooleanField(blank=True)
    crra_inf = models.FloatField(blank=True)
    crra_sup = models.FloatField(blank=True)
    crra_punto = models.FloatField(blank=True)
    categoria_riesgo = models.StringField(blank=True)

    # Pantalla 5: sorteos y pago
    tarea_pagada = models.IntegerField(blank=True)
    opcion_pagada = models.StringField(blank=True)
    numero_elegido = models.IntegerField(blank=True)
    premio_alto = models.BooleanField(blank=True)
    pago_ecu = models.IntegerField(blank=True)


# FUNCIONES

def pesos(x):
    """Formatea una cantidad en moneda local: 3850 -> '3.850 COP'."""
    return f'{x:,.0f}'.replace(',', '.') + ' COP'

CATEGORIAS = {
    0: 'Altamente amante del riesgo',
    1: 'Altamente amante del riesgo',
    2: 'Muy amante del riesgo',
    3: 'Amante del riesgo',
    4: 'Neutral al riesgo',
    5: 'Ligeramente averso al riesgo',
    6: 'Averso al riesgo',
    7: 'Muy averso al riesgo',
    8: 'Altamente averso al riesgo',
    9: 'Extremadamente averso al riesgo',
}
NO_CLASIFICABLE = 'No clasificable (elección dominada)'


def prob_alto(k):
    """Probabilidad del pago alto en la decisión k, en %."""
    return C.PASO_PROB * k


def utilidad(x, r):
    """Utilidad CRRA: x^(1-r)/(1-r), o ln(x) si r = 1."""
    if abs(r - 1) < 1e-9:
        return math.log(x)
    return x ** (1 - r) / (1 - r)


def umbral_crra(config, k):
    """
    r_(k): el coeficiente con el que una persona CRRA es indiferente entre A y B en la
    decisión k. Se calcula con los pagos de la sesión (búsqueda por bisección).
    """
    p = prob_alto(k) / 100

    def diferencia(r):
        a = p * utilidad(config['a_alto'], r) + (1 - p) * utilidad(config['a_bajo'], r)
        b = p * utilidad(config['b_alto'], r) + (1 - p) * utilidad(config['b_bajo'], r)
        return a - b

    bajo, alto = -10.0, 10.0
    if diferencia(bajo) * diferencia(alto) > 0:
        return None
    for _ in range(100):
        medio = (bajo + alto) / 2
        if diferencia(bajo) * diferencia(medio) <= 0:
            alto = medio
        else:
            bajo = medio
    return round((bajo + alto) / 2, 4)


def calcular_derivadas(player: Player):
    """Variables derivadas de las 10 decisiones (sección 4 del documento)."""
    config = player.session.config
    opciones = [getattr(player, f'opcion_{k}') for k in range(1, C.NUM_DECISIONES + 1)]

    player.num_seguras = opciones.count('A')
    cambios = [k for k in range(2, C.NUM_DECISIONES + 1) if opciones[k - 1] != opciones[k - 2]]
    player.num_cambios = len(cambios)
    if cambios:
        player.fila_cambio = cambios[0]
        player.direccion_cambio = 'A_a_B' if opciones[cambios[0] - 2] == 'A' else 'B_a_A'
    else:
        player.direccion_cambio = 'sin_cambio'
    player.elige_dominada = opciones[-1] == 'A'

    if player.elige_dominada:
        player.categoria_riesgo = NO_CLASIFICABLE
        return
    n = player.num_seguras
    if n > 0:
        player.crra_inf = umbral_crra(config, n)
    if n < C.NUM_DECISIONES - 1:
        player.crra_sup = umbral_crra(config, n + 1)
    inf, sup = player.field_maybe_none('crra_inf'), player.field_maybe_none('crra_sup')
    if inf is not None and sup is not None:
        player.crra_punto = round((inf + sup) / 2, 2)
    player.categoria_riesgo = CATEGORIAS[n]


def sortear_pago(player: Player):
    """Los dos sorteos del pago (sección 4, pasos 2 a 7)."""
    config = player.session.config
    player.tarea_pagada = random.randint(1, C.NUM_DECISIONES)
    player.opcion_pagada = getattr(player, f'opcion_{player.tarea_pagada}')
    player.numero_elegido = random.randint(1, C.SORTEO_MAX)
    player.premio_alto = player.numero_elegido <= prob_alto(player.tarea_pagada)
    if player.opcion_pagada == 'A':
        player.pago_ecu = config['a_alto'] if player.premio_alto else config['a_bajo']
    else:
        player.pago_ecu = config['b_alto'] if player.premio_alto else config['b_bajo']
    player.payoff = player.pago_ecu

# PÁGINAS

class Consentimiento(Page):
    form_model = 'player'
    form_fields = ['consentimiento']

    @staticmethod
    def error_message(player: Player, values):
        if not values['consentimiento']:
            return dict(consentimiento='Debe aceptar para participar')


class Instrucciones(Page):
    @staticmethod
    def vars_for_template(player: Player):
        config = player.session.config
        return dict(
            resto_1=100 - C.PASO_PROB,
            siguiente_1=C.PASO_PROB + 1,
            tasa=pesos(config['real_world_currency_per_point']),
            hay_pago_fijo=config['participation_fee'] > 0,
            pago_fijo=pesos(config['participation_fee']),
        )


class Practica(Page):
    form_model = 'player'
    form_fields = ['practica_eleccion']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(resto=100 - player.session.config['pract_prob'])

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        config = player.session.config
        player.practica_numero = random.randint(1, C.SORTEO_MAX)
        primero = player.practica_numero <= config['pract_prob']
        if player.practica_eleccion == 'X':
            player.practica_pago = config['pract_x_1'] if primero else config['pract_x_2']
        else:
            player.practica_pago = config['pract_y_1'] if primero else config['pract_y_2']


class PracticaResultado(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(resto=100 - player.session.config['pract_prob'])


class Decisiones(Page):
    form_model = 'player'
    form_fields = [f'opcion_{k}' for k in range(1, C.NUM_DECISIONES + 1)]

    @staticmethod
    def vars_for_template(player: Player):
        filas = []
        for k in range(1, C.NUM_DECISIONES + 1):
            filas.append(dict(k=k, campo=f'opcion_{k}', p=prob_alto(k), resto=100 - prob_alto(k)))
        return dict(filas=filas)

    @staticmethod
    def error_message(player: Player, values):
        opciones = [values[f'opcion_{k}'] for k in range(1, C.NUM_DECISIONES + 1)]
        cambios = sum(1 for a, b in zip(opciones, opciones[1:]) if a != b)
        if cambios > 1:
            return ('Solo puedes cambiar una vez entre la opción A y la opción B. '
                    'Revisa tus decisiones.')
        
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        calcular_derivadas(player)
        sortear_pago(player)


class Pago(Page):
    @staticmethod
    def vars_for_template(player: Player):
        config = player.session.config
        pago_moneda = float(player.payoff) * config['real_world_currency_per_point']
        return dict(
            pago_moneda=pesos(pago_moneda),
            hay_pago_fijo=config['participation_fee'] > 0,
            pago_total=pesos(pago_moneda + config['participation_fee']),
        )


page_sequence = [Consentimiento, Instrucciones, Practica, PracticaResultado, Decisiones, Pago]