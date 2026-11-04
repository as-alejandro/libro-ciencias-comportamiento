from otree.api import *
from utilidades import iniciar_cronometro, segundos_transcurridos


doc = """
Capítulo 8. Normas sociales. App 2: obtención de la dotación.
Marco "ganada": tarea de esfuerzo y confirmación. Marco "asignada": aviso de dotación asignada.
"""


class C(BaseConstants):
    NAME_IN_URL = 'dotacion'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    TIEMPO_TAREA = 120  # segundos (apartado 5)
    # Número de la opción correcta de cada pregunta de la tarea
    RESPUESTAS_CORRECTAS = dict(
        tarea_p1=3,
        tarea_p2=3,
        tarea_p3=2,
        tarea_p4=3,
        tarea_p5=3,
    )


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def pregunta(texto, opciones):
    """Crea una pregunta de opción múltiple. Las opciones se numeran desde 1."""
    return models.IntegerField(
        label=texto,
        choices=list(enumerate(opciones, start=1)),
        widget=widgets.RadioSelect,
        blank=True,
    )


class Player(BasePlayer):
    tarea_p1 = pregunta(
        '¿Cuál de estas palabras no pertenece al grupo?',
        ['uva', 'pera', 'zanahoria', 'manzana'],
    )
    tarea_p2 = pregunta(
        '¿Qué número sigue en la serie 2, 4, 8, 16…?',
        ['18', '24', '32', '64'],
    )
    tarea_p3 = pregunta(
        'Una camiseta cuesta 20 y tiene un 25% de descuento. ¿Cuánto pagas?',
        ['5', '15', '16', '18'],
    )
    tarea_p4 = pregunta(
        'Un tren sale a las 14:45 y el viaje dura 1 hora y 30 minutos. ¿A qué hora llega?',
        ['15:15', '16:00', '16:15', '16:30'],
    )
    tarea_p5 = pregunta(
        'María tiene el doble de edad que Juan. Juan tiene 15 años. '
        '¿Qué edad tendrá María dentro de 5 años?',
        ['25', '30', '35', '40'],
    )
    tarea_aciertos = models.IntegerField(blank=True)
    tarea_segundos = models.IntegerField(blank=True)
    tarea_superada = models.BooleanField(blank=True)


# FUNCIONES

def le_toca(player: Player, marco):
    """True si el participante aceptó participar y tiene el marco indicado."""
    return player.participant.consentimiento and player.participant.marco == marco


def corregir_tarea(player: Player):
    """Cuenta los aciertos y decide si se alcanzó el umbral."""
    aciertos = 0
    for campo, correcta in C.RESPUESTAS_CORRECTAS.items():
        if player.field_maybe_none(campo) == correcta:
            aciertos += 1
    player.tarea_aciertos = aciertos
    player.tarea_superada = aciertos >= player.session.config['umbral_tarea']


# PÁGINAS

class ExplicacionTarea(Page):
    @staticmethod
    def is_displayed(player: Player):
        return le_toca(player, 'ganada')


class Tarea(Page):
    form_model = 'player'
    form_fields = ['tarea_p1', 'tarea_p2', 'tarea_p3', 'tarea_p4', 'tarea_p5']
    timeout_seconds = C.TIEMPO_TAREA

    @staticmethod
    def is_displayed(player: Player):
        return le_toca(player, 'ganada')

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'tarea')
        return dict()

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.tarea_segundos = segundos_transcurridos(player, 'tarea')
        corregir_tarea(player)


class ConfirmacionTarea(Page):
    @staticmethod
    def is_displayed(player: Player):
        return le_toca(player, 'ganada')


class DotacionAsignada(Page):
    @staticmethod
    def is_displayed(player: Player):
        return le_toca(player, 'asignada')


page_sequence = [ExplicacionTarea, Tarea, ConfirmacionTarea, DotacionAsignada]