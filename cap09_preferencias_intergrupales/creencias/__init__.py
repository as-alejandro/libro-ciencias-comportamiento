from otree.api import *
from utilidades import iniciar_cronometro, segundos_transcurridos


doc = """
Capítulo 9. Preferencias intergrupales. App 5: creencias.
Predicción incentivada de cuánto devuelve, en promedio, un miembro del propio grupo
y uno del grupo contrario si recibe nivel_referencia_creencias ya multiplicado.
"""


class C(BaseConstants):
    NAME_IN_URL = 'creencias'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    control4 = models.IntegerField(widget=widgets.RadioSelect)
    control4_intentos = models.IntegerField(initial=0)
    creencias_propio = models.IntegerField(
        label='¿Cuánto crees que devolvería, en promedio?', min=0,
    )
    creencias_otro = models.IntegerField(
        label='¿Cuánto crees que devolvería, en promedio?', min=0,
    )
    creencias_propio_segundos = models.IntegerField(blank=True)
    creencias_otro_segundos = models.IntegerField(blank=True)


# FUNCIONES

def participa(player: Player):
    """True si el participante aceptó participar."""
    return player.participant.consentimiento


def recibido_referencia(player: Player):
    """Lo que recibe el receptor en el caso de referencia: monto × multiplicador."""
    config = player.session.config
    return config['nivel_referencia_creencias'] * config['multiplicador_confianza']


def creencias_propio_max(player: Player):
    return recibido_referencia(player)


def creencias_otro_max(player: Player):
    return recibido_referencia(player)


def control4_choices(player: Player):
    """Opciones del control 4. El valor de cada opción es el número que dice."""
    config = player.session.config
    etiqueta = config['etiqueta_moneda']
    enviado = config['nivel_referencia_creencias']
    recibido = recibido_referencia(player)
    opciones = [[enviado, f'{enviado} {etiqueta}'], [recibido, f'{recibido} {etiqueta}']]
    if recibido == enviado:  # con multiplicador 1 las dos opciones serían iguales
        opciones = opciones[:1]
    opciones.append([-1, 'Depende de lo que yo decida'])
    return opciones


def pantalla_aqui(player: Player, grupo, posicion):
    """
    True si la pregunta sobre 'grupo' ('propio' u 'otro') va en 'posicion'
    ('primero' o 'segundo') para este participante.
    """
    if not participa(player):
        return False
    primero = 'propio' if player.participant.orden_grupo_creencias == 'propio_primero' else 'otro'
    if posicion == 'primero':
        return grupo == primero
    return grupo != primero


# PÁGINAS

class Control4(Page):
    form_model = 'player'
    form_fields = ['control4']

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def error_message(player: Player, values):
        player.control4_intentos += 1
        if not player.session.config['exigir_controles']:
            return None
        if values['control4'] != recibido_referencia(player):
            return dict(control4='Esta respuesta no es correcta. Vuelve a intentarlo.')


class CreenciaPropio(Page):
    form_model = 'player'
    form_fields = ['creencias_propio']
    template_name = 'creencias/Creencia.html'

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'creencias_propio')
        return dict(es_propio=True, recibido=recibido_referencia(player))

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.creencias_propio_segundos = segundos_transcurridos(player, 'creencias_propio')


class CreenciaOtro(Page):
    form_model = 'player'
    form_fields = ['creencias_otro']
    template_name = 'creencias/Creencia.html'

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'creencias_otro')
        return dict(es_propio=False, recibido=recibido_referencia(player))

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.creencias_otro_segundos = segundos_transcurridos(player, 'creencias_otro')


class CreenciaPropioPrimero(CreenciaPropio):
    @staticmethod
    def is_displayed(player: Player):
        return pantalla_aqui(player, 'propio', 'primero')


class CreenciaOtroPrimero(CreenciaOtro):
    @staticmethod
    def is_displayed(player: Player):
        return pantalla_aqui(player, 'otro', 'primero')


class CreenciaPropioSegundo(CreenciaPropio):
    @staticmethod
    def is_displayed(player: Player):
        return pantalla_aqui(player, 'propio', 'segundo')


class CreenciaOtroSegundo(CreenciaOtro):
    @staticmethod
    def is_displayed(player: Player):
        return pantalla_aqui(player, 'otro', 'segundo')


page_sequence = [
    Control4,
    CreenciaPropioPrimero, CreenciaOtroPrimero,
    CreenciaPropioSegundo, CreenciaOtroSegundo,
]