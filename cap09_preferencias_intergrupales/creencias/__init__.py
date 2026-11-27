from otree.api import *
from utilidades import iniciar_cronometro, segundos_transcurridos, en_orden_aleatorio, error_entero, rango

doc = """
Capítulo 9. Preferencias intergrupales. App 5: creencias.
Escenario 4: Predicciones. Introducción, control 4 (dos preguntas) y dos predicciones
(propio grupo / otro grupo), en el orden de orden_grupo_creencias.
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
    # La pregunta 1 lleva números de los parámetros, así que se escribe en la plantilla
    control4_p1 = models.IntegerField(widget=widgets.RadioSelect, label='')
    control4_p2 = models.IntegerField(
        label='¿Qué tienes que predecir en las dos pantallas siguientes?',
        widget=widgets.RadioSelect,
    )
    control4_intentos = models.IntegerField(initial=0)
    # La pregunta se escribe en la plantilla, porque cambia según el grupo
    creencias_propio = models.IntegerField(label='', min=None, blank=True)
    creencias_otro = models.IntegerField(label='', min=None, blank=True)
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


def limites_creencia(player: Player, campo):
    return {campo: rango(0, recibido_referencia(player), 'Completa este campo.')}


def errores_creencia(player: Player, values, campo):
    error = error_entero(values[campo], 0, recibido_referencia(player), 'Completa este campo.')
    if error:
        return {campo: error}

def control4_p1_choices(player: Player):
    config = player.session.config
    etiqueta = config['etiqueta_moneda']
    enviado = config['nivel_referencia_creencias']
    recibido = recibido_referencia(player)
    opciones = [[enviado, f'{enviado} {etiqueta}'], [recibido, f'{recibido} {etiqueta}']]
    if recibido == enviado:
        opciones = opciones[:1]
    opciones.append([-1, 'Depende de lo que yo decida'])
    return en_orden_aleatorio(player, 'control4_p1', opciones)


def control4_p2_choices(player: Player):
    etiqueta = player.session.config['etiqueta_moneda']
    return en_orden_aleatorio(player, 'control4_p2', [
        [1, f'Cuántas {etiqueta} devolvieron, en promedio, las personas del grupo que se indique'],
        [2, f'Cuántas {etiqueta} devolví yo'],
        [3, f'Cuántas {etiqueta} enviaron las demás personas'],
    ])


def numero_de_pantalla(player: Player, grupo):
    """1 si la predicción sobre 'grupo' es la primera para este participante; 2 si no."""
    return 1 if pantalla_aqui(player, grupo, 'primero') else 2


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

class Introduccion(Page):
    @staticmethod
    def is_displayed(player: Player):
        return participa(player)


class Control4(Page):
    form_model = 'player'
    form_fields = ['control4_p1', 'control4_p2']

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(recibido=recibido_referencia(player))

    @staticmethod
    def error_message(player: Player, values):
        player.control4_intentos += 1
        if not player.session.config['exigir_controles']:
            return None
        correctas = dict(control4_p1=recibido_referencia(player), control4_p2=1)
        errores = {}
        for campo, correcta in correctas.items():
            if values[campo] != correcta:
                errores[campo] = 'Esta respuesta no es correcta. Vuelve a intentarlo.'
        return errores


class CreenciaPropio(Page):
    form_model = 'player'
    form_fields = ['creencias_propio']
    template_name = 'creencias/Creencia.html'

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'creencias_propio')
        return dict(es_propio=True, recibido=recibido_referencia(player),
                    numero=numero_de_pantalla(player, 'propio'),
                    rangos=limites_creencia(player, 'creencias_propio'))

    @staticmethod
    def error_message(player: Player, values):
        return errores_creencia(player, values, 'creencias_propio')
        
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
        return dict(es_propio=False, recibido=recibido_referencia(player),
                    numero=numero_de_pantalla(player, 'otro'),
                    rangos=limites_creencia(player, 'creencias_otro'))

    @staticmethod
    def error_message(player: Player, values):
        return errores_creencia(player, values, 'creencias_otro')
        
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
    Introduccion,
    Control4,
    CreenciaPropioPrimero, CreenciaOtroPrimero,
    CreenciaPropioSegundo, CreenciaOtroSegundo,
]