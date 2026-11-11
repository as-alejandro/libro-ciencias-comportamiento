from otree.api import *
import random
from utilidades import iniciar_cronometro, segundos_transcurridos


doc = """
Juego de bienes públicos con parámetros configurables desde settings.py:
tamaño del grupo, dotación inicial, tasa de retorno per cápita (MPCR),
número de rondas y tiempo para decidir. El multiplicador se calcula como
MPCR × tamaño del grupo, de modo que la MPCR no cambia al cambiar el tamaño
del grupo. Los grupos se forman al azar al inicio de cada ronda.
"""


class C(BaseConstants):
    NAME_IN_URL = 'bienes_publicos'
    PLAYERS_PER_GROUP = None  # los grupos se forman al inicio de cada ronda (FormarGrupos)
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
    aporte_por_tiempo = models.BooleanField(initial=False)
    segundos_decision = models.IntegerField(blank=True)
    segundos_instrucciones = models.IntegerField(blank=True)


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
        limite_tiempo=config['limite_tiempo'],
        tiempo_decision=config['tiempo_decision'],
        segundos_alerta=config['segundos_alerta'],
    )


def creating_session(subsession: Subsession):
    """Comprueba los parámetros al crear la sesión."""
    p = parametros(subsession.session)
    if p['num_rondas'] > C.NUM_ROUNDS:
        raise ValueError(f'El número de rondas no puede ser mayor que {C.NUM_ROUNDS}.')
    if p['limite_tiempo'] and not 0 < p['segundos_alerta'] < p['tiempo_decision']:
        raise ValueError(
            'El parámetro "segundos_alerta" debe ser mayor que 0 y menor que "tiempo_decision".'
        )
    if subsession.round_number == 1:
        for participante in subsession.session.get_participants():
            participante.en_juego = False


def formar_grupos(subsession: Subsession):
    """
    Se ejecuta al inicio de cada ronda, cuando todos han llegado.
    En la ronda 1 decide quién juega: quienes aceptaron, en grupos completos.
    En todas las rondas reparte al azar a quienes juegan en grupos nuevos.
    """
    tamano = subsession.session.config['tamano_grupo']
    jugadores = subsession.get_players()

    if subsession.round_number == 1:
        aceptaron = [j for j in jugadores if j.participant.consentimiento]
        random.shuffle(aceptaron)
        caben = len(aceptaron) - len(aceptaron) % tamano  # solo grupos completos
        for i, jugador in enumerate(aceptaron):
            jugador.participant.en_juego = i < caben

    en_juego = [j for j in jugadores if j.participant.en_juego]
    random.shuffle(en_juego)
    grupos = [en_juego[i:i + tamano] for i in range(0, len(en_juego), tamano)]
    fuera = [j for j in jugadores if not j.participant.en_juego]
    if fuera:
        grupos.append(fuera)  # quienes no juegan quedan juntos en un grupo aparte
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


def ronda_en_curso(player: Player):
    """True si esta ronda se juega (según num_rondas)."""
    return player.round_number <= player.session.config['num_rondas']


def juega(player: Player):
    """True si el participante juega esta ronda."""
    return player.participant.en_juego and ronda_en_curso(player)


# PÁGINAS

class FormarGrupos(WaitPage):
    wait_for_all_groups = True
    after_all_players_arrive = formar_grupos
    title_text = 'Formando los grupos'
    body_text = 'Espera un momento mientras se forman los grupos de esta ronda.'

    @staticmethod
    def is_displayed(player: Player):
        # En la ronda 1 esperan todos los que aceptaron; después, solo quienes juegan.
        if player.round_number == 1:
            return bool(player.participant.consentimiento)
        return juega(player)


class SinGrupo(Page):
    """Para quien aceptó pero no cabe en un grupo completo."""
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.round_number == 1
            and player.participant.consentimiento
            and not player.participant.en_juego
        )


class Instrucciones(Page):
    @staticmethod
    def is_displayed(player: Player):
        return juega(player) and player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'instrucciones')
        return parametros(player.session)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.segundos_instrucciones = segundos_transcurridos(player, 'instrucciones')


class Aportacion(Page):
    form_model = 'player'
    form_fields = ['aporte']
    timer_text = 'Tiempo restante para decidir:'

    @staticmethod
    def is_displayed(player: Player):
        return juega(player)

    @staticmethod
    def get_timeout_seconds(player: Player):
        config = player.session.config
        if config['limite_tiempo']:
            return config['tiempo_decision']
        return None  # sin límite de tiempo

    @staticmethod
    def vars_for_template(player: Player):
        nombre = f'decision_ronda_{player.round_number}'
        iniciar_cronometro(player, nombre)
        p = parametros(player.session)
        # Milisegundos que faltan para activar la alerta (aunque se recargue la página)
        transcurridos = segundos_transcurridos(player, nombre)
        p['ms_hasta_alerta'] = max(0, p['segundos_alerta'] - transcurridos) * 1000
        return p

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.segundos_decision = segundos_transcurridos(
            player, f'decision_ronda_{player.round_number}'
        )
        if timeout_happened:
            player.aporte = parametros(player.session)['dotacion']
            player.aporte_por_tiempo = True


class EsperaResultados(WaitPage):
    after_all_players_arrive = calcular_pagos
    title_text = 'Un momento, por favor'
    body_text = 'Esperando a que los demás miembros de tu grupo tomen su decisión.'

    @staticmethod
    def is_displayed(player: Player):
        return juega(player)


class Resultados(Page):
    @staticmethod
    def is_displayed(player: Player):
        return juega(player)

    @staticmethod
    def vars_for_template(player: Player):
        return parametros(player.session)


class Fin(Page):
    """Pantalla final para todos, después de la última ronda."""
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


page_sequence = [FormarGrupos, SinGrupo, Instrucciones, Aportacion, EsperaResultados, Resultados, Fin]