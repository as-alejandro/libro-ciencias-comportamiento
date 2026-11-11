from otree.api import *


doc = """
Juego de bienes públicos con parámetros configurables desde settings.py:
tamaño del grupo, dotación inicial, tasa de retorno per cápita (MPCR)
y número de rondas. El multiplicador se calcula como MPCR × tamaño del grupo,
de modo que la MPCR no cambia al cambiar el tamaño del grupo. \\

Adaptación de Tutotial oTree: https://otree.readthedocs.io/en/latest/tutorial/part2.html
"""


class C(BaseConstants):
    NAME_IN_URL = 'bienes_publicos'
    PLAYERS_PER_GROUP = None  # los grupos se forman en creating_session
    NUM_ROUNDS = 30  # máximo de rondas posible; las que se juegan vienen de settings.py


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    total_aportado = models.CurrencyField()
    ganancia_individual = models.CurrencyField()


class Player(BasePlayer):
    aporte = models.CurrencyField(
        min=0,
        label='¿Cuánto quieres aportar al fondo común?',
    )


# FUNCIONES

def parametros(session):
    """Lee los parámetros del juego desde la configuración de la sesión."""
    config = session.config
    tamano = config['tamano_grupo']
    mpcr = config['mpcr']
    return dict(
        tamano_grupo=tamano,
        dotacion=cu(config['dotacion']),
        mpcr=mpcr,
        multiplicador=round(mpcr * tamano, 2),
        num_rondas=config['num_rondas'],
    )


def creating_session(subsession: Subsession):
    """Comprueba los parámetros y forma los grupos (fijos en todas las rondas)."""
    p = parametros(subsession.session)
    tamano = p['tamano_grupo']
    jugadores = subsession.get_players()
    if len(jugadores) % tamano != 0:
        raise ValueError(
            f'El número de participantes ({len(jugadores)}) debe ser '
            f'múltiplo del tamaño del grupo ({tamano}).'
        )
    if p['num_rondas'] > C.NUM_ROUNDS:
        raise ValueError(f'El número de rondas no puede ser mayor que {C.NUM_ROUNDS}.')
    grupos = [jugadores[i:i + tamano] for i in range(0, len(jugadores), tamano)]
    subsession.set_group_matrix(grupos)


def aporte_max(player: Player):
    """Nadie puede aportar más que su dotación."""
    return parametros(player.session)['dotacion']


def calcular_pagos(group: Group):
    p = parametros(group.session)
    jugadores = group.get_players()
    group.total_aportado = sum(j.aporte for j in jugadores)
    group.ganancia_individual = (
        group.total_aportado * p['multiplicador'] / p['tamano_grupo']
    )
    for j in jugadores:
        j.payoff = p['dotacion'] - j.aporte + group.ganancia_individual


def ronda_activa(player: Player):
    """Solo se juegan las rondas indicadas en settings.py."""
    return player.round_number <= player.session.config['num_rondas']


# PÁGINAS

class Instrucciones(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return parametros(player.session)


class Aportacion(Page):
    form_model = 'player'
    form_fields = ['aporte']

    @staticmethod
    def is_displayed(player: Player):
        return ronda_activa(player)

    @staticmethod
    def vars_for_template(player: Player):
        return parametros(player.session)


class EsperaResultados(WaitPage):
    after_all_players_arrive = calcular_pagos

    @staticmethod
    def is_displayed(player: Player):
        return ronda_activa(player)


class Resultados(Page):
    @staticmethod
    def is_displayed(player: Player):
        return ronda_activa(player)

    @staticmethod
    def vars_for_template(player: Player):
        return parametros(player.session)


page_sequence = [Instrucciones, Aportacion, EsperaResultados, Resultados]