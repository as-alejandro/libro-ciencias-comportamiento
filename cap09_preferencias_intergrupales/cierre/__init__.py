from otree.api import *
from datetime import datetime
from utilidades import leer_niveles
import random


doc = """
Capítulo 9. Preferencias intergrupales. App 6: cierre.
Identificación con el grupo, cuestionario posterior, cálculo de pagos y resultado.
"""


class C(BaseConstants):
    NAME_IN_URL = 'cierre'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    NOMBRES_TAREAS = dict(
        dict_propio='tu reparto con alguien de tu propio grupo',
        dict_otro='tu reparto con alguien del grupo contrario',
        conf_emisor='lo que enviaste como emisor en el juego de confianza',
        conf_receptor='lo que devolviste como receptor en el juego de confianza',
        creencias_propio='tu predicción sobre tu propio grupo',
        creencias_otro='tu predicción sobre el grupo contrario',
    )


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    identificacion_valor = models.IntegerField(widget=widgets.RadioSelectHorizontal, label='')
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

    # Sorteo y pagos (se calculan cuando todos han terminado)
    seleccionado_pago = models.BooleanField(blank=True)
    tarea_pagada = models.StringField(blank=True)
    conf_pareja = models.StringField(blank=True)
    ganancia_fichas = models.IntegerField(blank=True)
    ganancia_local = models.FloatField(blank=True)
    n_sesion = models.IntegerField(blank=True)


# FUNCIONES

def participa(player: Player):
    """True si el participante aceptó participar."""
    return player.participant.consentimiento


def identificacion_valor_choices(player: Player):
    """Escala de 1 a k: solo los extremos llevan palabra (1 = nada, k = mucho)."""
    k = player.session.config['categorias_likert_identificacion']
    opciones = [[i, str(i)] for i in range(1, k + 1)]
    opciones[0][1] = '1 · Nada'
    opciones[-1][1] = f'{k} · Mucho'
    return opciones


def en_app(player, app):
    """El jugador de este participante en otra app ('dictador', 'confianza_estrategica'...)."""
    posicion = player.session.config['app_sequence'].index(app)
    return player.participant.get_players()[posicion]


def dato(player, app, campo):
    """Lee una respuesta de otra app; None si quedó vacía (por ejemplo, si alguien abandonó)."""
    return en_app(player, app).field_maybe_none(campo)


def relacion(uno, otro):
    """'propio' si los dos son del mismo grupo; 'otro' si no."""
    return 'propio' if uno.participant.grupo_asignado == otro.participant.grupo_asignado else 'otro'


def casilla_mas_cercana(niveles, monto):
    """
    Regla B1: número de casilla (1, 2, ...) del monto de la lista más cercano a 'monto'.
    Si hay empate, gana el monto menor.
    """
    posicion = min(range(len(niveles)), key=lambda i: (abs(niveles[i] - monto), niveles[i]))
    return posicion + 1


def enviado(emisor, receptor):
    """Lo que 'emisor' dijo que enviaría a alguien del grupo de 'receptor'."""
    return dato(emisor, 'confianza_estrategica', f'conf_emisor_{relacion(emisor, receptor)}')


def devuelto(receptor, emisor, monto, niveles, multiplicador):
    """
    Lo que 'receptor' devolvería si 'emisor' le envía 'monto': su respuesta para el monto
    más cercano de la tabla (regla B1), sin pasar nunca de lo que de verdad recibe.
    """
    casilla = casilla_mas_cercana(niveles, monto)
    respuesta = dato(receptor, 'confianza_estrategica',
                     f'conf_receptor_{relacion(receptor, emisor)}_{casilla}')
    if respuesta is None:
        return None
    return min(respuesta, monto * multiplicador)


def tiene_emisor(p):
    return all(dato(p, 'confianza_estrategica', f'conf_emisor_{g}') is not None
               for g in ['propio', 'otro'])


def tiene_receptor(p):
    return dato(p, 'confianza_estrategica', 'conf_receptor_propio_1') is not None


def devolucion_promedio(miembros, emisor, casilla_referencia):
    """
    Devolución promedio real de 'miembros' en el monto de referencia, frente a un emisor
    del grupo de 'emisor' (es decir, cómo tratarían a esa persona). None si no hay datos.
    """
    valores = []
    for m in miembros:
        campo = f'conf_receptor_{relacion(m, emisor)}_{casilla_referencia}'
        valor = dato(m, 'confianza_estrategica', campo)
        if valor is not None:
            valores.append(valor)
    if not valores:
        return None
    return sum(valores) / len(valores)


def calcular_pagos(subsession: Subsession):
    """Sorteos y ganancias de todos. Se ejecuta una vez, cuando todos han llegado a la espera."""
    config = subsession.session.config
    niveles = leer_niveles(config)
    multiplicador = config['multiplicador_confianza']
    casilla_referencia = niveles.index(config['nivel_referencia_creencias']) + 1
    semilla = config['semilla']
    azar = random.Random(semilla) if semilla else random.Random()

    # Solo cuentan quienes aceptaron participar
    jugadores = [p for p in subsession.get_players() if participa(p)]
    if not jugadores:
        return
    completaron = len([p for p in jugadores if p.field_maybe_none('claridad') is not None])

    # Quién cobra (solo con dinero real): todos, o 1 de cada prob_pago (al menos 1)
    if config['incentivos'] == 'dinero_real':
        if config['modo_pago'] == 'una_decision_propia':
            pagados = jugadores
        else:
            num_pagados = max(1, round(len(jugadores) / config['prob_pago']))
            pagados = azar.sample(jugadores, num_pagados)

    for p in jugadores:
        p.n_sesion = completaron
        if config['incentivos'] == 'dinero_real':
            p.seleccionado_pago = p in pagados
        otros = [q for q in jugadores if q != p]
        mi_grupo = [q for q in otros if relacion(q, p) == 'propio']
        grupo_contrario = [q for q in otros if relacion(q, p) == 'otro']

        # Qué decisiones se pueden evaluar para esta persona
        posibles = []
        for tarea in ['dict_propio', 'dict_otro']:
            if dato(p, 'dictador', f'{tarea}_cedido') is not None:
                posibles.append(tarea)
        receptores = [q for q in otros if tiene_receptor(q)]
        emisores = [q for q in otros if tiene_emisor(q)]
        if tiene_emisor(p) and receptores:
            posibles.append('conf_emisor')
        if tiene_receptor(p) and emisores:
            posibles.append('conf_receptor')
        for tarea, miembros in [('creencias_propio', mi_grupo), ('creencias_otro', grupo_contrario)]:
            if (dato(p, 'creencias', tarea) is not None
                    and devolucion_promedio(miembros, p, casilla_referencia) is not None):
                posibles.append(tarea)

        p.tarea_pagada = azar.choice(posibles) if posibles else 'ninguna'
        tarea = p.tarea_pagada
        ganancia = 0

        if tarea in ['dict_propio', 'dict_otro']:
            # Lo que se quedó en esa ronda
            ganancia = config['dotacion_dictador'] - dato(p, 'dictador', f'{tarea}_cedido')

        elif tarea == 'conf_emisor':
            # Otra persona al azar hace de receptora
            receptor = azar.choice(receptores)
            p.conf_pareja = receptor.participant.code
            monto = enviado(p, receptor)
            ganancia = config['dotacion_confianza'] - monto + devuelto(
                receptor, p, monto, niveles, multiplicador)

        elif tarea == 'conf_receptor':
            # Otra persona al azar hace de emisora
            emisor = azar.choice(emisores)
            p.conf_pareja = emisor.participant.code
            monto = enviado(emisor, p)
            ganancia = monto * multiplicador - devuelto(p, emisor, monto, niveles, multiplicador)

        elif tarea in ['creencias_propio', 'creencias_otro']:
            # Acierta si queda a 'tolerancia' o menos del promedio real de ese grupo
            miembros = mi_grupo if tarea == 'creencias_propio' else grupo_contrario
            real = devolucion_promedio(miembros, p, casilla_referencia)
            if abs(dato(p, 'creencias', tarea) - real) <= config['tolerancia_creencias']:
                ganancia = config['pago_creencias']

        p.ganancia_fichas = ganancia
        if config['incentivos'] == 'dinero_real':
            p.ganancia_local = ganancia * config['tasa_cambio']


# PÁGINAS

class Identificacion(Page):
    form_model = 'player'
    form_fields = ['identificacion_valor']

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)


class Cuestionario(Page):
    form_model = 'player'
    form_fields = ['edad', 'universidad', 'programa', 'semestre', 'claridad', 'comentario']

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.hora_fin = datetime.now().isoformat(timespec='seconds')


class EsperaFinal(WaitPage):
    wait_for_all_groups = True
    after_all_players_arrive = calcular_pagos
    title_text = 'Un momento'
    body_text = 'Estamos esperando a que todos terminen para calcular los resultados.'

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)


class Resultado(Page):
    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def vars_for_template(player: Player):
        config = player.session.config
        ganancia_local = player.field_maybe_none('ganancia_local')
        tarea = player.field_maybe_none('tarea_pagada') or 'ninguna'
        return dict(
            incentivos=config['incentivos'],
            sin_tarea=tarea == 'ninguna',
            nombre_tarea=C.NOMBRES_TAREAS.get(tarea, ''),
            ganancia_local=f'{ganancia_local:,.0f}'.replace(',', '.') if ganancia_local is not None else '',
            metodo=config['metodo_induccion_grupo'],
        )


class NoAcepta(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not participa(player)


page_sequence = [Identificacion, Cuestionario, EsperaFinal, Resultado, NoAcepta]