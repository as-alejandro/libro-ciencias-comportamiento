from otree.api import *
from datetime import datetime
from utilidades import leer_niveles, en_orden_aleatorio, iniciar_cronometro, segundos_transcurridos
import random


doc = """
Capítulo 9. Preferencias intergrupales. App 6: cierre.
Identificación con el grupo, cuestionario posterior, cálculo de pagos y resultado.
"""


class C(BaseConstants):
    NAME_IN_URL = 'cierre'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    # Nombres de los escenarios, en el orden de la actividad
    ESCENARIOS = {
        1: 'Repartir entre otras dos personas',
        2: 'Repartir entre tú y otra persona',
        3: 'Enviar y devolver',
        4: 'Predicciones',
    }


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def escala(desde, hasta):
    """Campo de escala numérica (por ejemplo, de 1 a 7). Las anclas se ponen en la plantilla."""
    return models.IntegerField(
        choices=list(range(desde, hasta + 1)),
        widget=widgets.RadioSelectHorizontal,
        label='',
        blank=True,
    )


class Player(BasePlayer):
    # Identificación con el grupo
    identificacion_grupo = escala(1, 7)
    identificacion_grupo_segundos = models.IntegerField(blank=True)

    # Cuestionario final (blank=True para mostrar nuestros propios mensajes de error)
    edad = models.IntegerField(label='Edad', min=None, blank=True)
    genero = models.StringField(
        label='¿Con qué género te identificas?',
        choices=['Mujer', 'Hombre', 'Otro', 'Prefiero no responder'],
        widget=widgets.RadioSelectHorizontal,
        blank=True,
    )
    universidad = models.StringField(label='Universidad', blank=True)
    programa = models.StringField(label='Programa o carrera', blank=True)
    semestre = models.StringField(
        label='Semestre',
        choices=[str(i) for i in range(1, 11)] + ['Más de 10', 'Posgrado'],
        blank=True,
    )
    grupo_recordado = models.StringField(
        label='¿A qué grupo fuiste asignado?',
        widget=widgets.RadioSelectHorizontal,
        blank=True,
    )
    grupo_recordado_correcto = models.BooleanField(blank=True)
    familiaridad_klee = escala(1, 7)
    familiaridad_kandinsky = escala(1, 7)
    influencia_grupo = models.StringField(
        label='Al decidir cuánto darle o enviarle a otra persona, ¿influyó de qué grupo era?',
        choices=['No', 'Sí'],
        widget=widgets.RadioSelectHorizontal,
        blank=True,
    )
    influencia_direccion = models.StringField(
        label='Comparado con una persona del otro grupo, con una persona de mi propio grupo…',
        choices=[
            'repartí o envié más',
            'repartí o envié menos',
            'busqué un reparto más equitativo',
            'otra forma',
        ],
        widget=widgets.RadioSelect,
        blank=True,
    )
    claridad = escala(1, 5)
    comentario = models.LongStringField(
        label='¿Quieres dejarnos algún comentario sobre la actividad?',
        blank=True,
    )
    hora_fin = models.StringField(blank=True)

    # Sorteo, emparejamiento y pagos (se calculan cuando todos han terminado)
    semilla_sorteo = models.IntegerField(blank=True)
    escenario_sorteado = models.IntegerField(blank=True)
    rol = models.StringField(blank=True)
    pareja_codigos = models.StringField(blank=True)
    pareja_grupos = models.StringField(blank=True)
    decision_aplicada = models.StringField(blank=True)
    sobrante = models.BooleanField(blank=True)
    ganancia_fichas = models.IntegerField(blank=True)
    n_sesion = models.IntegerField(blank=True)


# FUNCIONES

def participa(player: Player):
    """True si el participante aceptó participar."""
    return player.participant.consentimiento


def grupo_recordado_choices(player: Player):
    return en_orden_aleatorio(player, 'grupo_recordado', ['Klee', 'Kandinsky'])


def en_app(player, app):
    """El jugador de este participante en otra app ('dictador', 'confianza_estrategica'...)."""
    posicion = player.session.config['app_sequence'].index(app)
    return player.participant.get_players()[posicion]


def dato(player, app, campo):
    """Lee una respuesta de otra app; None si quedó vacía."""
    return en_app(player, app).field_maybe_none(campo)


def relacion(uno, otro):
    """'propio' si los dos son del mismo grupo; 'otro' si no."""
    return 'propio' if uno.participant.grupo_asignado == otro.participant.grupo_asignado else 'otro'


def grupo(p):
    return p.participant.grupo_asignado


def decimal(x):
    """12.5 -> '12,5'; 12.0 -> '12'."""
    texto = f'{x:.1f}'.replace('.', ',')
    return texto[:-2] if texto.endswith(',0') else texto


def formar_parejas(jugadores, azar):
    """
    Parejas al azar entre todos. Con un número impar, el sobrante se empareja con
    alguien que ya tiene pareja (solo el sobrante cobra por ese emparejamiento extra).
    Devuelve una lista de (persona, pareja, cobra_la_pareja).
    """
    orden = list(jugadores)
    azar.shuffle(orden)
    parejas = []
    for i in range(0, len(orden) - 1, 2):
        parejas.append((orden[i], orden[i + 1], True))
    if len(orden) % 2 == 1:
        sobrante = orden[-1]
        parejas.append((sobrante, azar.choice(orden[:-1]), False))
    return parejas


def escenario_1(jugadores, config, azar):
    """Reparto circular: cada persona reparte entre las dos siguientes de una lista al azar."""
    etiqueta = config['etiqueta_moneda']
    orden = list(jugadores)
    azar.shuffle(orden)
    n = len(orden)
    recibido = {p: [] for p in orden}  # montos que le asignan a cada persona
    for i, p in enumerate(orden):
        a, b = orden[(i + 1) % n], orden[(i + 2) % n]
        caso = relacion(p, a) + '_' + relacion(p, b)
        if caso == 'propio_propio' or caso == 'otro_otro':
            monto_a = dato(p, 'espectador', f'espectador_{caso}_1')
            monto_b = dato(p, 'espectador', f'espectador_{caso}_2')
            situacion = ('las dos eran de tu propio grupo' if caso == 'propio_propio'
                         else 'las dos eran del otro grupo')
        else:
            caso = 'mixto'
            propio = dato(p, 'espectador', 'espectador_mixto_propio')
            otro = dato(p, 'espectador', 'espectador_mixto_otro')
            monto_a, monto_b = (propio, otro) if relacion(p, a) == 'propio' else (otro, propio)
            situacion = 'una era de tu propio grupo y la otra del otro grupo'
        recibido[a].append(monto_a)
        recibido[b].append(monto_b)
        p.rol = 'reparte'
        p.pareja_codigos = f'reparte a: {a.participant.code}, {b.participant.code}'
        p.pareja_grupos = f'reparte a: {grupo(a)}, {grupo(b)}'
        p.decision_aplicada = f'{caso}: {monto_a} a {a.participant.code}, {monto_b} a {b.participant.code}'
        p.participant.vars['aplicada'] = (
            f'Repartiste entre dos personas: {situacion}. Le diste {monto_a} {etiqueta} a '
            f'una persona del grupo {grupo(a)} y {monto_b} a una persona del grupo {grupo(b)}.'
        )
    for i, p in enumerate(orden):
        de_1, de_2 = orden[(i - 1) % n], orden[(i - 2) % n]
        p.pareja_codigos += f'; recibe de: {de_2.participant.code}, {de_1.participant.code}'
        p.pareja_grupos += f'; recibe de: {grupo(de_2)}, {grupo(de_1)}'
        a, b = recibido[p]
        p.ganancia_fichas = a + b
        p.participant.vars['calculo'] = (
            f'{etiqueta.capitalize()} que te asignaron las dos personas que te precedían en la '
            f'lista: {a} + {b} = {a + b}.'
        )
    for p in orden:
        repartos = {caso: [dato(p, 'espectador', f'espectador_{caso}_{i}') for i in (1, 2)]
                    for caso in ['propio_propio', 'otro_otro']}
        p.participant.vars['tomadas'] = (
            f'Las dos de tu propio grupo: {repartos["propio_propio"][0]} y '
            f'{repartos["propio_propio"][1]}. Las dos del otro grupo: {repartos["otro_otro"][0]} y '
            f'{repartos["otro_otro"][1]}. Una de cada grupo: '
            f'{dato(p, "espectador", "espectador_mixto_propio")} a la de tu propio grupo y '
            f'{dato(p, "espectador", "espectador_mixto_otro")} a la del otro grupo.'
        )


def escenario_2(jugadores, config, azar):
    """Dictador: parejas al azar; en cada una, un rol al azar."""
    etiqueta = config['etiqueta_moneda']
    dotacion = config['dotacion_dictador']
    for p in jugadores:
        p.participant.vars['tomadas'] = (
            f'A una persona de tu propio grupo le dabas {dato(p, "dictador", "dict_propio_cedido")} '
            f'{etiqueta}; a una del otro grupo, {dato(p, "dictador", "dict_otro_cedido")}.'
        )
    for uno, otro, cobra_otro in formar_parejas(jugadores, azar):
        decide, recibe = (uno, otro) if azar.random() < 0.5 else (otro, uno)
        cedido = dato(decide, 'dictador', f'dict_{relacion(decide, recibe)}_cedido')
        cobran = [uno, otro] if cobra_otro else [uno]
        if decide in cobran:
            decide.rol = 'decide'
            decide.pareja_codigos = recibe.participant.code
            decide.pareja_grupos = grupo(recibe)
            decide.decision_aplicada = f'dict_{relacion(decide, recibe)}_cedido = {cedido}'
            decide.ganancia_fichas = dotacion - cedido
            decide.participant.vars['aplicada'] = (
                f'Te tocó decidir. Tu pareja era del grupo {grupo(recibe)}, así que se aplicó tu '
                f'decisión para ese caso: le diste {cedido} {etiqueta}.'
            )
            decide.participant.vars['calculo'] = f'{dotacion} − {cedido} = {dotacion - cedido}.'
        if recibe in cobran:
            recibe.rol = 'recibe'
            recibe.pareja_codigos = decide.participant.code
            recibe.pareja_grupos = grupo(decide)
            recibe.decision_aplicada = f'recibió {cedido}'
            recibe.ganancia_fichas = cedido
            recibe.participant.vars['aplicada'] = (
                f'Te tocó recibir. Tu pareja era del grupo {grupo(decide)} y te dio '
                f'{cedido} {etiqueta}.'
            )
            recibe.participant.vars['calculo'] = f'Recibiste {cedido}.'
        if not cobra_otro:
            uno.sobrante = True


def escenario_3(jugadores, config, azar):
    """Confianza: parejas al azar; en cada una, un rol al azar."""
    etiqueta = config['etiqueta_moneda']
    dotacion = config['dotacion_confianza']
    multiplicador = config['multiplicador_confianza']
    niveles = leer_niveles(config)
    for p in jugadores:
        devoluciones = []
        for i, nivel in enumerate(niveles, start=1):
            if nivel == 0:
                continue
            devoluciones.append(
                f'si te enviaban {nivel}, devolvías '
                f'{dato(p, "confianza_estrategica", f"conf_receptor_propio_{i}")} a tu propio grupo y '
                f'{dato(p, "confianza_estrategica", f"conf_receptor_otro_{i}")} al otro grupo'
            )
        p.participant.vars['tomadas'] = (
            f'Como quien envía: {dato(p, "confianza_estrategica", "conf_emisor_propio")} a tu propio '
            f'grupo y {dato(p, "confianza_estrategica", "conf_emisor_otro")} al otro grupo. '
            f'Como quien recibe: ' + '; '.join(devoluciones) + '.'
        )
    for uno, otro, cobra_otro in formar_parejas(jugadores, azar):
        envia, recibe = (uno, otro) if azar.random() < 0.5 else (otro, uno)
        monto = dato(envia, 'confianza_estrategica', f'conf_emisor_{relacion(envia, recibe)}')
        if monto == 0:
            devolucion = 0
        else:
            casilla = niveles.index(monto) + 1
            devolucion = dato(recibe, 'confianza_estrategica',
                              f'conf_receptor_{relacion(recibe, envia)}_{casilla}')
        cobran = [uno, otro] if cobra_otro else [uno]
        if envia in cobran:
            envia.rol = 'envia'
            envia.pareja_codigos = recibe.participant.code
            envia.pareja_grupos = grupo(recibe)
            envia.decision_aplicada = f'envió {monto}, le devolvieron {devolucion}'
            envia.ganancia_fichas = dotacion - monto + devolucion
            envia.participant.vars['aplicada'] = (
                f'Te tocó enviar. Tu pareja era del grupo {grupo(recibe)}, así que se aplicó tu '
                f'decisión para ese caso: enviaste {monto} {etiqueta}, tu pareja recibió '
                f'{monto * multiplicador} y te devolvió {devolucion}.'
            )
            envia.participant.vars['calculo'] = (
                f'{dotacion} − {monto} + {devolucion} = {envia.ganancia_fichas}.'
            )
        if recibe in cobran:
            recibe.rol = 'recibe'
            recibe.pareja_codigos = envia.participant.code
            recibe.pareja_grupos = grupo(envia)
            recibe.decision_aplicada = f'recibió {monto * multiplicador}, devolvió {devolucion}'
            recibe.ganancia_fichas = monto * multiplicador - devolucion
            recibe.participant.vars['aplicada'] = (
                f'Te tocó recibir. Tu pareja era del grupo {grupo(envia)} y te envió {monto} '
                f'{etiqueta}, así que recibiste {monto * multiplicador}. Según tu decisión para ese '
                f'caso, devolviste {devolucion}.'
            )
            recibe.participant.vars['calculo'] = (
                f'{monto * multiplicador} − {devolucion} = {recibe.ganancia_fichas}.'
            )
        if not cobra_otro:
            uno.sobrante = True


def promedio_real(jugadores, quien_predice, evaluado, config):
    """
    Devolución promedio, al nivel de referencia, de los receptores del grupo evaluado
    ('propio' u 'otro', visto desde quien predice), cuando quien envía es del grupo de
    quien predice. No incluye a quien predice. None si no hay nadie con quien calcularlo.
    """
    niveles = leer_niveles(config)
    casilla = niveles.index(config['nivel_referencia_creencias']) + 1
    valores = []
    for q in jugadores:
        if q == quien_predice or relacion(quien_predice, q) != evaluado:
            continue
        # Desde el receptor q, quien envía es de su propio grupo o del otro
        campo = f'conf_receptor_{relacion(q, quien_predice)}_{casilla}'
        valores.append(dato(q, 'confianza_estrategica', campo))
    if not valores:
        return None
    return sum(valores) / len(valores)


def escenario_4(jugadores, config):
    """Predicciones: sin emparejamiento."""
    etiqueta = config['etiqueta_moneda']
    premio = config['premio_creencias']
    umbral = config['umbral_creencias']
    nombres = dict(propio='de tu propio grupo', otro='del otro grupo')
    for p in jugadores:
        prediccion = {g: dato(p, 'creencias', f'creencias_{g}') for g in ['propio', 'otro']}
        aciertos = 0
        aplicada = []
        registro = []
        for g in ['propio', 'otro']:
            real = promedio_real(jugadores, p, g, config)
            if real is None:
                aplicada.append(f'No hubo datos para calcular el promedio real {nombres[g]}.')
                registro.append(f'{g}: sin datos')
                continue
            diferencia = abs(prediccion[g] - real)
            acierto = diferencia <= umbral
            aciertos += acierto
            aplicada.append(
                f'Promedio real {nombres[g]}: {decimal(real)} (tu predicción se diferencia en '
                f'{decimal(diferencia)}{", dentro del umbral" if acierto else ""}).'
            )
            registro.append(f'{g}: real {decimal(real)}, dif {decimal(diferencia)}')
        p.rol = 'predice'
        p.decision_aplicada = '; '.join(registro)
        p.ganancia_fichas = aciertos * premio
        p.participant.vars['tomadas'] = (
            f'Tu predicción sobre tu propio grupo: {prediccion["propio"]}; sobre el otro grupo: '
            f'{prediccion["otro"]}.'
        )
        p.participant.vars['aplicada'] = ' '.join(aplicada)
        p.participant.vars['calculo'] = (
            f'{premio} {etiqueta} por cada predicción a {umbral} o menos del promedio real: '
            f'{aciertos} × {premio} = {p.ganancia_fichas}.'
        )


def calcular_pagos(subsession: Subsession):
    """
    Se ejecuta una vez, cuando todos han llegado a la espera final. Sortea un escenario
    para toda la sesión y calcula el emparejamiento y las ganancias de ese escenario.
    """
    config = subsession.session.config
    jugadores = [p for p in subsession.get_players() if participa(p)]
    if not jugadores:
        return

    # Semilla: la de los parámetros, o una nueva al azar; se guarda para poder repetir el sorteo
    semilla = config['semilla'] or random.SystemRandom().randrange(1, 10**9)
    azar = random.Random(semilla)

    # El escenario 1 necesita al menos 3 personas y los escenarios 2 y 3, al menos 2
    n = len(jugadores)
    posibles = [e for e, minimo in [(1, 3), (2, 2), (3, 2), (4, 1)] if n >= minimo]
    escenario = azar.choice(posibles)

    for p in jugadores:
        p.semilla_sorteo = semilla
        p.escenario_sorteado = escenario
        p.n_sesion = n
        p.sobrante = False

    if escenario == 1:
        escenario_1(jugadores, config, azar)
    elif escenario == 2:
        escenario_2(jugadores, config, azar)
    elif escenario == 3:
        escenario_3(jugadores, config, azar)
    else:
        escenario_4(jugadores, config)


# PÁGINAS

# Campos obligatorios del cuestionario y el mensaje si quedan vacíos
OBLIGATORIAS_CUESTIONARIO = dict(
    edad='Ingresa tu edad como un número entero.',
    genero='Elige una de las opciones.',
    universidad='Completa este campo.',
    programa='Completa este campo.',
    semestre='Elige una de las opciones.',
    grupo_recordado='Elige una de las opciones.',
    familiaridad_klee='Elige una de las opciones.',
    familiaridad_kandinsky='Elige una de las opciones.',
    influencia_grupo='Elige una de las opciones.',
    claridad='Elige una de las opciones.',
)


class Identificacion(Page):
    form_model = 'player'
    form_fields = ['identificacion_grupo']

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'identificacion_grupo')
        return dict()

    @staticmethod
    def error_message(player: Player, values):
        if values['identificacion_grupo'] is None:
            return dict(identificacion_grupo='Elige una de las opciones.')

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.identificacion_grupo_segundos = segundos_transcurridos(player, 'identificacion_grupo')


class Cuestionario(Page):
    form_model = 'player'
    form_fields = ['edad', 'genero', 'universidad', 'programa', 'semestre', 'grupo_recordado',
                   'familiaridad_klee', 'familiaridad_kandinsky', 'influencia_grupo',
                   'influencia_direccion', 'claridad', 'comentario']
    
    @staticmethod
    def vars_for_template(player: Player):
        # La edad usa un solo mensaje para todos los errores (vacía, decimal o fuera de rango)
        mensaje = OBLIGATORIAS_CUESTIONARIO['edad']
        return dict(rangos=dict(edad=dict(min=15, max=99, vacio=mensaje, unico=mensaje)))

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def error_message(player: Player, values):
        errores = {}
        for campo, mensaje in OBLIGATORIAS_CUESTIONARIO.items():
            valor = values[campo]
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                errores[campo] = mensaje
        edad = values['edad']
        if edad is not None and not 15 <= edad <= 99:
            errores['edad'] = 'Ingresa tu edad como un número entero.'
        # La pregunta de seguimiento solo es obligatoria si respondió «Sí»
        if values['influencia_grupo'] == 'Sí' and values['influencia_direccion'] is None:
            errores['influencia_direccion'] = 'Elige una de las opciones.'
        return errores

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.influencia_grupo == 'No':
            player.influencia_direccion = None  # por si marcó algo antes de cambiar a «No»
        player.grupo_recordado_correcto = (
            player.grupo_recordado == player.participant.grupo_asignado
        )
        player.hora_fin = datetime.now().isoformat(timespec='seconds')


class EsperaFinal(WaitPage):
    wait_for_all_groups = True
    after_all_players_arrive = calcular_pagos
    title_text = 'Espera un momento'
    body_text = 'Estamos esperando a que todos terminen la actividad.'

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)


class Resultado(Page):
    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def vars_for_template(player: Player):
        escenario = player.escenario_sorteado
        datos = player.participant.vars
        return dict(
            escenario=escenario,
            nombre_escenario=C.ESCENARIOS[escenario],
            tomadas=datos.get('tomadas', ''),
            aplicada=datos.get('aplicada', ''),
            calculo=datos.get('calculo', ''),
        )


class NoAcepta(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not participa(player)


page_sequence = [Identificacion, Cuestionario, EsperaFinal, Resultado, NoAcepta]
