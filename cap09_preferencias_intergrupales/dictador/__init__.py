from otree.api import *
from utilidades import iniciar_cronometro, segundos_transcurridos, error_entero, rango

doc = """
Capítulo 9. Preferencias intergrupales. App 3: dictador.
Escenario 2: Repartir entre tú y otra persona. Pantalla de introducción y dos repartos
de la dotación (otra persona del propio grupo / del otro grupo), en el orden asignado
a cada participante.
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
    # La pregunta se escribe en la plantilla, porque lleva números de los parámetros
    # min=None y blank=True: los límites y los mensajes los pone limites_dictador
    dict_propio_cedido = models.IntegerField(label='', min=None, blank=True)
    dict_otro_cedido = models.IntegerField(label='', min=None, blank=True)
    dict_propio_segundos = models.IntegerField(blank=True)
    dict_otro_segundos = models.IntegerField(blank=True)


# FUNCIONES

def participa(player: Player):
    """True si el participante aceptó participar."""
    return player.participant.consentimiento


def limites_dictador(player: Player, campo):
    """Rango permitido y mensaje si queda vacío, para el campo 'campo'."""
    config = player.session.config
    vacio = f'Indica cuántas {config["etiqueta_moneda"]} le das a la otra persona.'
    return {campo: rango(0, config['dotacion_dictador'], vacio)}


def errores_dictador(player: Player, values, campo):
    r = limites_dictador(player, campo)[campo]
    error = error_entero(values[campo], r['min'], r['max'], r['vacio'])
    if error:
        return {campo: error}


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

def numero_de_pantalla(player: Player, contraparte):
    """1 si la ronda con 'contraparte' es la primera para este participante; 2 si no."""
    return 1 if ronda_aqui(player, contraparte, 'primero') else 2

# PÁGINAS
class Introduccion(Page):
    @staticmethod
    def is_displayed(player: Player):
        return participa(player)
    
class RondaPropio(Page):
    form_model = 'player'
    form_fields = ['dict_propio_cedido']
    template_name = 'dictador/Ronda.html'

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'dict_propio')
        return dict(es_propio=True, numero=numero_de_pantalla(player, 'propio'),
                    rangos=limites_dictador(player, 'dict_propio_cedido'))

    @staticmethod
    def error_message(player: Player, values):
        return errores_dictador(player, values, 'dict_propio_cedido')
        
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
        return dict(es_propio=False, numero=numero_de_pantalla(player, 'otro'),
                    rangos=limites_dictador(player, 'dict_otro_cedido'))

    @staticmethod
    def error_message(player: Player, values):
        return errores_dictador(player, values, 'dict_otro_cedido')
        
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


page_sequence = [Introduccion, RondaPropioPrimero, RondaOtroPrimero, RondaPropioSegundo, RondaOtroSegundo]