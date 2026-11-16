from otree.api import *
from utilidades import iniciar_cronometro, segundos_transcurridos


doc = """
Capítulo 9. Preferencias intergrupales. App 3: dictador.
Dos repartos de la dotación: uno con alguien del propio grupo y otro con alguien
del grupo contrario, en el orden asignado a cada participante.
"""


class C(BaseConstants):
    NAME_IN_URL = 'dictador'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    dict_propio_cedido = models.IntegerField(
        label='¿Cuántas le das a la otra persona?', min=0,
    )
    dict_otro_cedido = models.IntegerField(
        label='¿Cuántas le das a la otra persona?', min=0,
    )
    dict_propio_segundos = models.IntegerField(blank=True)
    dict_otro_segundos = models.IntegerField(blank=True)


# FUNCIONES

def participa(player: Player):
    """True si el participante aceptó participar."""
    return player.participant.consentimiento


def dict_propio_cedido_max(player: Player):
    return player.session.config['dotacion_dictador']


def dict_otro_cedido_max(player: Player):
    return player.session.config['dotacion_dictador']


def ronda_aqui(player: Player, contraparte, posicion):
    """
    True si la ronda con 'contraparte' ('propio' u 'otro') va en 'posicion'
    ('primero' o 'segundo') para este participante.
    """
    if not participa(player):
        return False
    primera = 'propio' if player.participant.orden_contraparte_dictador == 'propio_primero' else 'otro'
    if posicion == 'primero':
        return contraparte == primera
    return contraparte != primera


# PÁGINAS

class RondaPropio(Page):
    form_model = 'player'
    form_fields = ['dict_propio_cedido']
    template_name = 'dictador/Ronda.html'

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'dict_propio')
        return dict(es_propio=True)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.dict_propio_segundos = segundos_transcurridos(player, 'dict_propio')


class RondaOtro(Page):
    form_model = 'player'
    form_fields = ['dict_otro_cedido']
    template_name = 'dictador/Ronda.html'

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'dict_otro')
        return dict(es_propio=False)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.dict_otro_segundos = segundos_transcurridos(player, 'dict_otro')


class RondaPropioPrimero(RondaPropio):
    @staticmethod
    def is_displayed(player: Player):
        return ronda_aqui(player, 'propio', 'primero')


class RondaOtroPrimero(RondaOtro):
    @staticmethod
    def is_displayed(player: Player):
        return ronda_aqui(player, 'otro', 'primero')


class RondaPropioSegundo(RondaPropio):
    @staticmethod
    def is_displayed(player: Player):
        return ronda_aqui(player, 'propio', 'segundo')


class RondaOtroSegundo(RondaOtro):
    @staticmethod
    def is_displayed(player: Player):
        return ronda_aqui(player, 'otro', 'segundo')


page_sequence = [RondaPropioPrimero, RondaOtroPrimero, RondaPropioSegundo, RondaOtroSegundo]