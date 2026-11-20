import random
from collections import Counter

from otree.api import *
from utilidades import leer_repartos


doc = """
Capítulo 8. Normas sociales. App 4: cierre.
Cuestionario posterior, cálculo de pagos (cuando todos han terminado) y resultado.
"""


class C(BaseConstants):
    NAME_IN_URL = 'cierre'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    NOMBRES_TAREAS = dict(
        bx='la predicción de lo que respondieron los demás',
        kw='la calificación de los repartos',
        ee='la predicción de lo que harían los demás',
        decision='tu decisión de reparto',
    )


class Subsession(BaseSubsession):
    pass


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

    # Sorteo y pagos (se calculan cuando todos han terminado)
    seleccionado_pago = models.BooleanField(blank=True)
    tarea_pagada = models.StringField(blank=True)
    kw_accion_sorteada = models.IntegerField(blank=True)
    pareja_id = models.StringField(blank=True)
    ganancia_fichas = models.IntegerField(blank=True)
    ganancia_local = models.FloatField(blank=True)


# FUNCIONES

def respuestas(player: Player):
    """Devuelve el jugador de la app 'normas', donde están las respuestas de la actividad."""
    return player.participant.get_players()[2]


def respuesta(jugador_normas, campo):
    """Lee un campo de 'normas'; devuelve None si quedó vacío (por ejemplo, si alguien abandonó)."""
    return jugador_normas.field_maybe_none(campo)


def modas(valores):
    """Conjunto de los valores más frecuentes (más de uno si hay empate). Vacío si no hay valores."""
    valores = [v for v in valores if v is not None]
    if not valores:
        return set()
    conteo = Counter(valores)
    maximo = max(conteo.values())
    return {valor for valor, veces in conteo.items() if veces == maximo}


def tareas_hechas(jugador_normas):
    """Tareas incentivadas que hizo este participante y que se pueden sortear para el pago."""
    tareas = []
    if respuesta(jugador_normas, 'bx_norma_personal') is not None:
        tareas.append('bx')
    if respuesta(jugador_normas, 'kw_calif_1') is not None:
        tareas.append('kw')
    if respuesta(jugador_normas, 'ee_1') is not None:
        tareas.append('ee')
    if respuesta(jugador_normas, 'decision') is not None:
        tareas.append('decision')
    return tareas


def calcular_pagos(subsession: Subsession):
    """Sorteos y ganancias de todos. Se ejecuta una vez, cuando todos han llegado a la espera."""
    config = subsession.session.config
    repartos = leer_repartos(config)
    n_repartos = len(repartos)
    tolerancia = config['tolerancia_prediccion']

    # Solo cuentan quienes aceptaron participar
    jugadores = [p for p in subsession.get_players() if p.participant.consentimiento]
    if not jugadores:
        return
    normas = {p.id_in_subsession: respuestas(p) for p in jugadores}

    # 1. Quién cobra: 1 de cada prob_pago participantes (al menos 1)
    num_pagados = max(1, round(len(jugadores) / config['prob_pago']))
    pagados = random.sample(jugadores, num_pagados)

    # 2. Parejas: cada decisión afecta a la siguiente persona en un círculo al azar.
    #    Así nadie queda sin pareja, aunque el número sea impar.
    orden = jugadores[:]
    random.shuffle(orden)
    for i, p in enumerate(orden):
        receptor = orden[(i + 1) % len(orden)]
        if receptor != p:
            p.pareja_id = receptor.participant.code

    for p in jugadores:
        mio = normas[p.id_in_subsession]
        otros = [normas[q.id_in_subsession] for q in jugadores if q != p]

        p.seleccionado_pago = p in pagados
        p.kw_accion_sorteada = random.randint(1, n_repartos)
        accion = p.kw_accion_sorteada

        tareas = tareas_hechas(mio)
        p.tarea_pagada = random.choice(tareas) if tareas else 'ninguna'

        ganancia = 0
        if p.tarea_pagada == 'bx':
            # Acierta si su reparto más votado coincide con el más votado por los demás
            moda_real = modas([respuesta(o, 'bx_norma_personal') for o in otros])
            if respuesta(mio, 'bx_moda_predicha') in moda_real:
                ganancia = config['pago_bx']

        elif p.tarea_pagada == 'kw':
            # Acierta si su calificación del reparto sorteado coincide con la más frecuente de los demás
            campo = f'kw_calif_{accion}'
            moda_real = modas([respuesta(o, campo) for o in otros])
            if respuesta(mio, campo) in moda_real:
                ganancia = config['pago_kw']

        elif p.tarea_pagada == 'ee':
            # Acierta si su predicción para el reparto sorteado está a 'tolerancia' o menos
            # de lo que de verdad eligieron los demás, llevado a una escala de 10 personas
            decisiones = [respuesta(o, 'decision') for o in otros]
            decisiones = [d for d in decisiones if d is not None]
            if decisiones:
                real = round(10 * decisiones.count(accion) / len(decisiones))
                prediccion = respuesta(mio, f'ee_{accion}')
                if prediccion is not None and abs(prediccion - real) <= tolerancia:
                    ganancia = config['pago_ee']

        elif p.tarea_pagada == 'decision':
            # Gana lo que decidió quedarse
            queda, da = repartos[respuesta(mio, 'decision') - 1]
            ganancia = queda

        p.ganancia_fichas = ganancia
        if config['incentivos'] == 'monetario':
            p.ganancia_local = ganancia * config['tasa_cambio']


# PÁGINAS

class Cuestionario(Page):
    form_model = 'player'
    form_fields = ['edad', 'universidad', 'programa', 'semestre', 'claridad', 'comentario']

    @staticmethod
    def is_displayed(player: Player):
        return player.participant.consentimiento


class EsperaFinal(WaitPage):
    wait_for_all_groups = True
    after_all_players_arrive = calcular_pagos
    title_text = 'Un momento'
    body_text = 'Estamos esperando a que todos terminen para calcular los resultados.'

    @staticmethod
    def is_displayed(player: Player):
        return player.participant.consentimiento


class Resultado(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.participant.consentimiento

    @staticmethod
    def vars_for_template(player: Player):
        config = player.session.config
        ganancia_local = player.field_maybe_none('ganancia_local')
        return dict(
            hipotetico=config['incentivos'] == 'hipotetico',
            monetario=config['incentivos'] == 'monetario',
            nombre_tarea=C.NOMBRES_TAREAS.get(player.field_maybe_none('tarea_pagada'), ''),
            ganancia_local=f'{ganancia_local:,.0f}'.replace(',', '.') if ganancia_local is not None else '',
        )


class NoAcepta(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not player.participant.consentimiento


page_sequence = [Cuestionario, EsperaFinal, Resultado, NoAcepta]