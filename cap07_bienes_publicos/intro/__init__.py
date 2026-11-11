from otree.api import *
from datetime import datetime


doc = """
Capítulo 7. Bienes públicos. App 1: consentimiento informado.
"""


class C(BaseConstants):
    NAME_IN_URL = 'intro_bp'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


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


page_sequence = [Consentimiento]