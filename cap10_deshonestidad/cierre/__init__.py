from otree.api import *
from datetime import datetime
import random


doc = """
Capítulo 10. Deshonestidad: declaración de ingresos. App 4: cierre.
Cuestionario posterior, sorteo de la ronda pagada y resultado.
"""


class C(BaseConstants):
    NAME_IN_URL = 'cierre'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    ronda_pagada = models.IntegerField(blank=True)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    edad = models.IntegerField(label='Edad', min=15, max=99, blank=True)
    universidad = models.StringField(label='Universidad', blank=True)
    programa = models.StringField(label='Programa o carrera', blank=True)
    semestre = models.StringField(label='Semestre', blank=True)
    claridad = models.IntegerField(
        label='¿Qué tan claras te parecieron las instrucciones de la actividad?',
        choices=[
            [1, '1 · Nada claras'],
            [2, '2'],
            [3, '3'],
            [4, '4'],
            [5, '5 · Muy claras'],
        ],
        widget=widgets.RadioSelectHorizontal,
    )
    comentario = models.LongStringField(
        label='¿Quieres dejarnos algún comentario sobre la actividad?',
        blank=True,
    )
    hora_fin = models.StringField(blank=True)

    # Sorteo y pago (se calculan cuando todos han terminado)
    ronda_pagada = models.IntegerField(blank=True)
    pago_ronda_sorteada = models.FloatField(blank=True)
    seleccionado_pago = models.BooleanField(blank=True)
    ganancia = models.FloatField(blank=True)
    ganancia_local = models.FloatField(blank=True)


# FUNCIONES

def en_juego(player: Player):
    """True si el participante jugó las rondas en un grupo completo."""
    return bool(player.participant.vars.get('en_juego'))


def numero(x):
    """Muestra un número sin decimales si es entero (15) y con coma si no (9,25)."""
    x = round(x, 2)
    if x == int(x):
        return str(int(x))
    return str(x).replace('.', ',')


def calcular_pagos(subsession: Subsession):
    """
    Se ejecuta una vez, cuando todos los que jugaron llegan a la espera.
    Sortea una ronda (la misma para todos) y, con dinero real, quién cobra.
    """
    config = subsession.session.config
    semilla = config['semilla']
    azar = random.Random(f'{semilla}-cierre') if semilla else random.Random()

    jugadores = [p for p in subsession.get_players() if en_juego(p)]
    if not jugadores:
        return

    subsession.ronda_pagada = azar.randint(1, config['num_rondas'])

    # Con dinero real se paga a 1 de cada prob_pago (al menos 1); en los otros modos, a todos
    if config['incentivos'] == 'monetario':
        num_pagados = max(1, round(len(jugadores) / config['prob_pago']))
        pagados = azar.sample(jugadores, num_pagados)
    else:
        pagados = jugadores

    for p in jugadores:
        p.ronda_pagada = subsession.ronda_pagada
        pago = p.participant.vars.get('pagos_rondas', {}).get(str(p.ronda_pagada), 0)
        p.pago_ronda_sorteada = pago
        p.ganancia = max(0, pago)  # el pago no puede ser negativo
        p.seleccionado_pago = p in pagados
        if config['incentivos'] == 'monetario':
            p.ganancia_local = p.ganancia * config['tasa_cambio']


# PÁGINAS

class Cuestionario(Page):
    form_model = 'player'
    form_fields = ['edad', 'universidad', 'programa', 'semestre', 'claridad', 'comentario']

    @staticmethod
    def is_displayed(player: Player):
        return en_juego(player)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.hora_fin = datetime.now().isoformat(timespec='seconds')


class EsperaFinal(WaitPage):
    wait_for_all_groups = True
    after_all_players_arrive = calcular_pagos
    title_text = 'Un momento'
    body_text = 'Estamos esperando a que todos terminen para sortear la ronda que se paga.'

    @staticmethod
    def is_displayed(player: Player):
        return en_juego(player)


class Resultado(Page):
    @staticmethod
    def is_displayed(player: Player):
        return en_juego(player)

    @staticmethod
    def vars_for_template(player: Player):
        local = player.field_maybe_none('ganancia_local')
        return dict(
            incentivos=player.session.config['incentivos'],
            pago=numero(player.pago_ronda_sorteada),
            negativo=player.pago_ronda_sorteada < 0,
            ganancia=numero(player.ganancia),
            ganancia_local=f'{local:,.0f}'.replace(',', '.') if local is not None else '',
        )


class SinGrupo(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.participant.consentimiento and not en_juego(player)


class NoAcepta(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not player.participant.consentimiento


page_sequence = [Cuestionario, EsperaFinal, Resultado, SinGrupo, NoAcepta]