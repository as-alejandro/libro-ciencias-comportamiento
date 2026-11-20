from otree.api import *
from datetime import datetime


doc = """
Capítulo 10. Deshonestidad: declaración de ingresos. App 1: introducción.
Comprobación de parámetros y consentimiento.
"""


class C(BaseConstants):
    NAME_IN_URL = 'intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


VALORES_VALIDOS = dict(
    incentivos=['hipotetico', 'puntos', 'monetario'],
    tratamiento=['aleatorio', 'control', 'sin_explicacion', 'inversion', 'salarios'],
)

PORCENTAJES = ['impuesto_total', 'impuesto_fondo', 'impuesto_admin', 'impuesto_extra',
               'prob_auditoria']


def comprobar_parametros(config):
    """Detiene la creación de la sesión si algún parámetro no es válido."""
    for parametro, validos in VALORES_VALIDOS.items():
        if config[parametro] not in validos:
            raise ValueError(
                f'El parámetro "{parametro}" tiene el valor "{config[parametro]}", '
                f'que no es válido. Valores posibles: {", ".join(validos)}.'
            )
    for parametro in PORCENTAJES:
        if not 0 <= config[parametro] <= 100:
            raise ValueError(f'"{parametro}" es un porcentaje: tiene que estar entre 0 y 100.')

    # Los tratamientos con aumento solo se revisan si pueden aparecer en la sesión
    if config['tratamiento'] != 'control':
        suma = config['impuesto_fondo'] + config['impuesto_admin'] + config['impuesto_extra']
        if config['impuesto_extra'] <= 0:
            raise ValueError(
                'En los tratamientos con aumento, "impuesto_extra" tiene que ser mayor que 0.'
            )
        if config['impuesto_total'] != suma:
            raise ValueError(
                f'Los porcentajes del impuesto no encajan: impuesto_fondo + impuesto_admin + '
                f'impuesto_extra = {config["impuesto_fondo"]} + {config["impuesto_admin"]} + '
                f'{config["impuesto_extra"]} = {suma}, pero impuesto_total es '
                f'{config["impuesto_total"]}. Tienen que ser iguales.'
            )

    if config['tamano_grupo'] < 2:
        raise ValueError('"tamano_grupo" tiene que ser 2 o más.')
    if not 1 <= config['num_rondas'] <= 20:
        raise ValueError('"num_rondas" tiene que estar entre 1 y 20.')
    if config['multa'] < 0:
        raise ValueError('"multa" no puede ser negativa.')
    if config['multiplicador'] < 1:
        raise ValueError('"multiplicador" tiene que ser 1 o más.')
    if config['prob_pago'] < 1:
        raise ValueError('"prob_pago" tiene que ser 1 o más.')
    if config['segundos_tarea'] < 5:
        raise ValueError('"segundos_tarea" tiene que ser 5 o más.')


def creating_session(subsession: Subsession):
    comprobar_parametros(subsession.session.config)


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


# PÁGINAS

class Consentimiento(Page):
    form_model = 'player'
    form_fields = ['consentimiento']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.consentimiento = player.consentimiento
        if player.consentimiento:
            player.hora_inicio = datetime.now().isoformat(timespec='seconds')


class InstruccionesGenerales(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.consentimiento

    @staticmethod
    def vars_for_template(player: Player):
        return dict(otros=player.session.config['tamano_grupo'] - 1)


page_sequence = [Consentimiento, InstruccionesGenerales]