from otree.api import *
import random
from utilidades import iniciar_cronometro, segundos_transcurridos


doc = """
Capítulo 10. Deshonestidad: declaración de ingresos. App 3: declaración.
Ronda 1: se forman los grupos (fijos para todas las rondas) y se asigna un tratamiento
por grupo. Quienes no completan un grupo no participan. En cada ronda: declaración,
impuesto, auditoría, fondo público y resultado.
"""


class C(BaseConstants):
    NAME_IN_URL = 'declaracion'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 20  # máximo; la sesión usa solo num_rondas
    TRATAMIENTOS = ['control', 'sin_explicacion', 'inversion', 'salarios']


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    tratamiento = models.StringField(blank=True)
    aporte_total = models.FloatField(blank=True)
    fondo_generado = models.FloatField(blank=True)


class Player(BasePlayer):
    # Control de comprensión (solo en la ronda 1)
    control_p1 = models.FloatField(widget=widgets.RadioSelect, label='')
    control_p2 = models.IntegerField(
        label='',
        choices=[
            [1, 'Se suma al fondo público y aumenta lo que recibe el grupo'],
            [2, 'No regresa al grupo: no aumenta el fondo público'],
            [3, 'Se reparte entre los miembros del grupo que declararon todo'],
        ],
        widget=widgets.RadioSelect,
    )
    control_p3 = models.FloatField(widget=widgets.RadioSelect, label='')
    control_intentos = models.IntegerField(initial=0)
    
    # Cada ronda
    ingreso = models.IntegerField(blank=True)
    info_promedio_otros = models.FloatField(blank=True)  # solo con info_social, desde la ronda 2
    declarado = models.IntegerField(label='¿Cuánto de tu ingreso deseas declarar?', min=0)
    declaracion_segundos = models.IntegerField(blank=True)
    impuesto_pagado = models.FloatField(blank=True)
    aporte_fondo = models.FloatField(blank=True)
    auditado = models.BooleanField(blank=True)
    impuesto_adicional = models.FloatField(blank=True)
    multa = models.FloatField(blank=True)
    pago_fondo = models.FloatField(blank=True)
    pago_ronda = models.FloatField(blank=True)


# FUNCIONES

def en_juego(player: Player):
    """
    True si el participante quedó en un grupo completo. Se usa vars.get porque
    quien no aceptó pasa por aquí antes de que se formen los grupos.
    """
    return bool(player.participant.vars.get('en_juego'))


def formar_grupos(subsession: Subsession):
    """
    Se ejecuta una vez, cuando todos llegan a la espera de la ronda 1.
    Forma grupos completos al azar entre quienes aceptaron, los deja fijos
    en todas las rondas y le asigna un tratamiento a cada grupo.
    """
    config = subsession.session.config
    tamano = config['tamano_grupo']
    semilla = config['semilla']
    azar = random.Random(semilla) if semilla else random.Random()

    aceptaron = [p for p in subsession.get_players() if p.participant.consentimiento]
    azar.shuffle(aceptaron)
    cuantos = len(aceptaron) // tamano * tamano
    dentro = aceptaron[:cuantos]
    fuera = aceptaron[cuantos:] + [p for p in subsession.get_players()
                                  if not p.participant.consentimiento]

    # Matriz de grupos: los completos primero; los que sobran, juntos en un grupo aparte
    grupos = [dentro[i:i + tamano] for i in range(0, cuantos, tamano)]
    matriz = [[p.id_in_subsession for p in grupo] for grupo in grupos]
    if fuera:
        matriz.append([p.id_in_subsession for p in fuera])

    # Un tratamiento por grupo completo, repartidos como un mazo barajado
    if config['tratamiento'] == 'aleatorio':
        tratamientos = []
        while len(tratamientos) < len(grupos):
            mazo = C.TRATAMIENTOS.copy()
            azar.shuffle(mazo)
            tratamientos.extend(mazo)
    else:
        tratamientos = [config['tratamiento']] * len(grupos)

    # Los mismos grupos y tratamientos en todas las rondas
    for ronda in subsession.in_rounds(1, C.NUM_ROUNDS):
        ronda.set_group_matrix(matriz)
        for numero, grupo in enumerate(ronda.get_groups()):
            if numero < len(grupos):
                grupo.tratamiento = tratamientos[numero]

    for p in dentro:
        p.participant.en_juego = True
        p.participant.tratamiento = p.group.tratamiento
    for p in fuera:
        p.participant.en_juego = False


def numero(x):
    """Muestra un número sin decimales si es entero (15) y con coma si no (9,25)."""
    x = round(x, 2)
    if x == int(x):
        return str(int(x))
    return str(x).replace('.', ',')


def impuesto(player: Player):
    """
    Los porcentajes del impuesto que se le aplican a este participante, según el
    tratamiento de su grupo. En control no hay parte extra.
    """
    config = player.session.config
    destino = player.participant.tratamiento
    fondo = config['impuesto_fondo']
    admin = config['impuesto_admin']
    if destino == 'control':
        extra = 0
        total = fondo + admin
    else:
        extra = config['impuesto_extra']
        total = config['impuesto_total']
    return dict(destino=destino, total=total, fondo=fondo, admin=admin, extra=extra)


def textos_instrucciones(player: Player):
    """Todos los números que aparecen en las instrucciones, ya calculados."""
    config = player.session.config
    imp = impuesto(player)
    tamano = config['tamano_grupo']
    fondo_ejemplo = 80 * config['multiplicador']

    def parte(declarado, porcentaje):
        return numero(declarado * porcentaje / 100)

    return dict(
        imp=imp,
        # Ejemplos del impuesto con ingreso 100: declarar 100 y declarar 60
        ej100=dict(total=parte(100, imp['total']), fondo=parte(100, imp['fondo']),
                   admin=parte(100, imp['admin']), extra=parte(100, imp['extra'])),
        ej60=dict(total=parte(60, imp['total']), fondo=parte(60, imp['fondo']),
                  admin=parte(60, imp['admin']), extra=parte(60, imp['extra'])),
        # Ejemplo de la multa: ingreso 100, declara 60, oculta 40
        multa_ejemplo=parte(40, config['multa']),
        impuesto_oculto_ejemplo=parte(40, imp['total']),
        # Ejemplo del fondo: el grupo aporta 80
        fondo_ejemplo=numero(fondo_ejemplo),
        reparto_ejemplo=numero(fondo_ejemplo / tamano),
        otros=tamano - 1,
    )


def control_p1_choices(player: Player):
    """Opciones de la pregunta 1. El valor de cada opción es el propio número."""
    imp = impuesto(player)
    opciones = [60 * imp['total'] / 100, 100 * imp['total'] / 100, 60 * imp['fondo'] / 100]
    vistas = []
    for valor in opciones:
        if valor not in [v for v, _ in vistas]:
            vistas.append([valor, f'{numero(valor)} {player.session.config["etiqueta_moneda"]}'])
    return vistas


def control_p3_choices(player: Player):
    config = player.session.config
    m, n = config['multiplicador'], config['tamano_grupo']
    opciones = [80 * m / n, 80 / n, 80 * m]
    vistas = []
    for valor in opciones:
        if valor not in [v for v, _ in vistas]:
            vistas.append([valor, f'{numero(valor)} {config["etiqueta_moneda"]}'])
    return vistas


def correctas_control(player: Player):
    config = player.session.config
    return dict(
        control_p1=60 * impuesto(player)['total'] / 100,
        control_p2=2,
        control_p3=80 * config['multiplicador'] / config['tamano_grupo'],
    )

def ronda_activa(player: Player):
    """True si esta ronda se juega (no pasa de num_rondas) y el participante está en un grupo."""
    return player.round_number <= player.session.config['num_rondas'] and en_juego(player)


def declarado_max(player: Player):
    return player.participant.ingreso


def promedio_otros_ronda_anterior(player: Player):
    """
    Porcentaje promedio de su ingreso que declararon los otros miembros del grupo en la
    ronda anterior. None si no hay datos (por ejemplo, si todos tenían ingreso 0).
    """
    anteriores = [o.in_round(player.round_number - 1) for o in player.get_others_in_group()]
    porcentajes = [100 * o.declarado / o.ingreso for o in anteriores
                   if o.field_maybe_none('declarado') is not None and o.ingreso]
    if not porcentajes:
        return None
    return round(sum(porcentajes) / len(porcentajes), 1)


def calcular_ronda(group: Group):
    """Impuestos, auditorías, fondo y pago de la ronda. Se ejecuta cuando el grupo termina."""
    config = group.session.config
    semilla = config['semilla']
    azar = random.Random(f'{semilla}-{group.round_number}-{group.id_in_subsession}') if semilla else random.Random()
    jugadores = group.get_players()

    for p in jugadores:
        imp = impuesto(p)
        declarado = p.field_maybe_none('declarado') or 0  # 0 si abandonó y el docente lo avanzó
        oculto = p.ingreso - declarado
        p.impuesto_pagado = round(declarado * imp['total'] / 100, 2)
        p.aporte_fondo = round(declarado * imp['fondo'] / 100, 2)
        p.auditado = azar.random() < config['prob_auditoria'] / 100
        if p.auditado and oculto > 0:
            p.impuesto_adicional = round(oculto * imp['total'] / 100, 2)
            p.multa = round(oculto * config['multa'] / 100, 2)
        else:
            p.impuesto_adicional = 0
            p.multa = 0

    group.aporte_total = round(sum(p.aporte_fondo for p in jugadores), 2)
    group.fondo_generado = round(group.aporte_total * config['multiplicador'], 2)
    reparto = round(group.fondo_generado / len(jugadores), 2)

    for p in jugadores:
        p.pago_fondo = reparto
        p.pago_ronda = round(p.ingreso - p.impuesto_pagado - p.impuesto_adicional
                             - p.multa + p.pago_fondo, 2)
        # Se guarda también en el participante, para que el cierre pueda sortear una ronda
        pagos = dict(p.participant.vars.get('pagos_rondas', {}))
        pagos[str(group.round_number)] = p.pago_ronda
        p.participant.vars['pagos_rondas'] = pagos

def primera_ronda(player: Player):
    return player.round_number == 1 and en_juego(player)


# PÁGINAS

class FormarGrupos(WaitPage):
    wait_for_all_groups = True
    after_all_players_arrive = formar_grupos
    title_text = 'Un momento'
    body_text = 'Estamos formando los grupos. Esto tomará unos segundos.'

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1 and player.participant.consentimiento


class Instrucciones(Page):
    """Página madre de las tres pantallas de instrucciones (solo en la ronda 1)."""

    @staticmethod
    def is_displayed(player: Player):
        return primera_ronda(player)

    @staticmethod
    def vars_for_template(player: Player):
        return textos_instrucciones(player)


class InstruccionesImpuesto(Instrucciones):
    pass


class InstruccionesAuditoria(Instrucciones):
    pass


class InstruccionesFondo(Instrucciones):
    pass


class Control(Page):
    form_model = 'player'
    form_fields = ['control_p1', 'control_p2', 'control_p3']

    @staticmethod
    def is_displayed(player: Player):
        return primera_ronda(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(tamano=player.session.config['tamano_grupo'])

    @staticmethod
    def error_message(player: Player, values):
        player.control_intentos += 1
        if not player.session.config['exigir_controles']:
            return None
        errores = {}
        for campo, correcta in correctas_control(player).items():
            if abs(values[campo] - correcta) > 0.001:
                errores[campo] = 'Esta respuesta no es correcta. Vuelve a intentarlo.'
        return errores


class Declaracion(Page):
    form_model = 'player'
    form_fields = ['declarado']

    @staticmethod
    def is_displayed(player: Player):
        return ronda_activa(player)

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, f'declaracion_{player.round_number}')
        player.ingreso = player.participant.ingreso
        config = player.session.config
        mostrar_info = config['info_social'] and player.round_number > 1
        if mostrar_info:
            player.info_promedio_otros = promedio_otros_ronda_anterior(player)
        promedio = player.field_maybe_none('info_promedio_otros')
        return dict(
            imp=impuesto(player),
            mostrar_info=mostrar_info,
            hay_promedio=promedio is not None,
            promedio=numero(promedio) if promedio is not None else '',
            otros=config['tamano_grupo'] - 1,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.declaracion_segundos = segundos_transcurridos(player, f'declaracion_{player.round_number}')


class EsperaGrupo(WaitPage):
    after_all_players_arrive = calcular_ronda
    title_text = 'Un momento'
    body_text = 'Estamos esperando a que los demás miembros de tu grupo tomen su decisión.'

    @staticmethod
    def is_displayed(player: Player):
        return ronda_activa(player)


class ResultadoRonda(Page):
    @staticmethod
    def is_displayed(player: Player):
        return ronda_activa(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            impuesto_pagado=numero(player.impuesto_pagado),
            aporte_fondo=numero(player.aporte_fondo),
            impuesto_adicional=numero(player.impuesto_adicional),
            multa=numero(player.multa),
            aporte_total=numero(player.group.aporte_total),
            fondo_generado=numero(player.group.fondo_generado),
            pago_fondo=numero(player.pago_fondo),
            pago_ronda=numero(player.pago_ronda),
        )


page_sequence = [FormarGrupos, InstruccionesImpuesto, InstruccionesAuditoria,
                 InstruccionesFondo, Control, Declaracion, EsperaGrupo, ResultadoRonda]