from otree.api import *


doc = """
Capítulo 9. Preferencias intergrupales. App 2: revelación del grupo.
Se comunica a cada participante su grupo (A o B) y se comprueba que entiende
qué significa "tu propio grupo" y "el grupo contrario".
"""


class C(BaseConstants):
    NAME_IN_URL = 'revelacion_grupo'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    control2_p1 = models.IntegerField(
        label='En las siguientes pantallas, cuando te digamos que la otra persona es '
              '«de tu propio grupo», ¿qué significa?',
        widget=widgets.RadioSelect,
    )
    control2_p2 = models.IntegerField(
        label='¿Y cuando te digamos que es «del grupo contrario»?',
        widget=widgets.RadioSelect,
    )
    control2_intentos = models.IntegerField(initial=0)


# FUNCIONES

def participa(player: Player):
    """True si el participante aceptó participar."""
    return player.participant.consentimiento


def grupos(player: Player):
    """Devuelve (mi grupo, el otro grupo), por ejemplo ('A', 'B')."""
    propio = player.participant.grupo_asignado
    otro = 'B' if propio == 'A' else 'A'
    return propio, otro


def opciones_control2(player: Player):
    """Las mismas tres opciones para las dos preguntas del control 2."""
    propio, otro = grupos(player)
    return [
        [1, 'Que es una persona de la clase que yo conozco'],
        [2, f'Que es un participante anónimo del grupo {propio}, igual que yo'],
        [3, f'Que es un participante anónimo del grupo {otro}'],
    ]


def control2_p1_choices(player: Player):
    return opciones_control2(player)


def control2_p2_choices(player: Player):
    return opciones_control2(player)


# Respuesta correcta de cada pregunta del control 2
CORRECTAS_CONTROL2 = dict(control2_p1=2, control2_p2=3)


# PÁGINAS

class TuGrupo(Page):
    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            grupo=player.participant.grupo_asignado,
            por_sorteo=player.session.config['metodo_induccion_grupo'] == 'moneda',
        )


class Control2(Page):
    form_model = 'player'
    form_fields = ['control2_p1', 'control2_p2']

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def error_message(player: Player, values):
        player.control2_intentos += 1
        if not player.session.config['exigir_controles']:
            return None
        errores = {}
        for campo, respuesta in values.items():
            if respuesta != CORRECTAS_CONTROL2[campo]:
                errores[campo] = 'Esta respuesta no es correcta. Vuelve a intentarlo.'
        return errores


page_sequence = [TuGrupo, Control2]