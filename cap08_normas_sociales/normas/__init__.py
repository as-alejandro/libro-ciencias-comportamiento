from otree.api import *
from utilidades import iniciar_cronometro, segundos_transcurridos, leer_repartos


doc = """
Capítulo 8. Normas sociales. App 3: medición de la norma (BX y KW),
expectativas empíricas y decisión real, en el orden asignado a cada participante.
"""


class C(BaseConstants):
    NAME_IN_URL = 'normas'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def prediccion():
    """Casilla para repartir fichas de una predicción: un número entre 0 y 10."""
    return models.IntegerField(min=0, max=10, blank=True)


class Player(BasePlayer):
    # Método BX: creencia normativa personal
    bx_norma_personal = models.IntegerField(
        label='En tu opinión, ¿cuál de estos repartos es el apropiado en esta situación?',
        widget=widgets.RadioSelect,
    )

    # Expectativas empíricas: una casilla por reparto (hasta 5 repartos)
    ee_1 = prediccion()
    ee_2 = prediccion()
    ee_3 = prediccion()
    ee_4 = prediccion()
    ee_5 = prediccion()
    ee_segundos = models.IntegerField(blank=True)

    decision = models.IntegerField(
        label='¿Qué reparto eliges?',
        widget=widgets.RadioSelect,
    )
    decision_segundos = models.IntegerField(blank=True)


# FUNCIONES

def participa(player: Player):
    """True si el participante aceptó participar."""
    return player.participant.consentimiento


def opciones_reparto(player: Player):
    """Lista de opciones (número, texto) en el formato 'quedarse con X y dar Y'."""
    config = player.session.config
    etiqueta = config['etiqueta_moneda']
    return [
        (i, f'Quedarse con {queda} {etiqueta} y dar {da} {etiqueta}')
        for i, (queda, da) in enumerate(leer_repartos(config), start=1)
    ]


def decision_choices(player: Player):
    return opciones_reparto(player)



def bx_norma_personal_choices(player: Player):
    return opciones_reparto(player)


def usa_metodo(player: Player, metodo):
    """True si al participante le toca el método indicado ('bx' o 'kw')."""
    return player.participant.metodo in [metodo, 'ambos']


def bloque_norma_aqui(player: Player, momento):
    """
    True si el bloque de creencias (norma y expectativas) va en este momento
    para el participante: 'antes' o 'despues' de la decisión.
    """
    if not participa(player):
        return False
    if momento == 'antes':
        return player.participant.orden_bloques == 'norma_primero'
    return player.participant.orden_bloques == 'decision_primero'

def campos_prediccion(player: Player, prefijo):
    """Nombres de las casillas que se usan según el número de repartos: ee_1, ee_2..."""
    n = len(leer_repartos(player.session.config))
    return [f'{prefijo}_{i}' for i in range(1, n + 1)]

def comprobar_suma_10(values, campos):
    """Mensaje de error si las fichas no suman exactamente 10; None si están bien."""
    if any(values[campo] is None for campo in campos):
        return 'Escribe un número en todas las casillas (puede ser 0).'
    total = sum(values[campo] for campo in campos)
    if total < 10:
        faltan = 10 - total
        verbo = 'falta' if faltan == 1 else 'faltan'
        return f'Las fichas tienen que sumar exactamente 10. Te {verbo} {faltan}.'
    if total > 10:
        sobran = total - 10
        verbo = 'sobra' if sobran == 1 else 'sobran'
        return f'Las fichas tienen que sumar exactamente 10. Te {verbo} {sobran}.'
    return None


# PÁGINAS


class BXPersonal(Page):
    form_model = 'player'
    form_fields = ['bx_norma_personal']
    template_name = 'normas/BXPersonal.html'

    @staticmethod
    def vars_for_template(player: Player):
        return dict(opciones=[texto for numero, texto in opciones_reparto(player)])


class BXPersonalAntes(BXPersonal):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'antes') and usa_metodo(player, 'bx')


class BXPersonalDespues(BXPersonal):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'despues') and usa_metodo(player, 'bx')

class Expectativas(Page):
    form_model = 'player'
    template_name = 'normas/Expectativas.html'

    @staticmethod
    def get_form_fields(player: Player):
        return campos_prediccion(player, 'ee')

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'expectativas')
        campos = campos_prediccion(player, 'ee')
        textos = [texto for numero, texto in opciones_reparto(player)]
        return dict(filas=list(zip(campos, textos)))

    @staticmethod
    def error_message(player: Player, values):
        return comprobar_suma_10(values, campos_prediccion(player, 'ee'))

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.ee_segundos = segundos_transcurridos(player, 'expectativas')


class ExpectativasAntes(Expectativas):
    """Expectativas cuando la norma se mide antes de decidir."""
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'antes')


class ExpectativasDespues(Expectativas):
    """Expectativas cuando la norma se mide después de decidir."""
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'despues')

class Decision(Page):
    form_model = 'player'
    form_fields = ['decision']

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'decision')
        return dict()

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.decision_segundos = segundos_transcurridos(player, 'decision')


page_sequence = [
    # Bloque de creencias, si va antes de la decisión
    BXPersonalAntes,
    ExpectativasAntes,
    # Decisión real
    Decision,
    # Bloque de creencias, si va después de la decisión
    BXPersonalDespues,
    ExpectativasDespues,
]