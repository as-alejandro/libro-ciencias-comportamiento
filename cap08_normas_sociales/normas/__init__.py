from otree.api import *
from utilidades import (
    iniciar_cronometro, segundos_transcurridos, leer_repartos, ESCALAS_KW, valor_kw
)


doc = """
Capítulo 8. Normas sociales. App 3: medición de la norma (BX y KW),
expectativas empíricas y decisión real, en el orden asignado a cada participante.
"""


class C(BaseConstants):
    NAME_IN_URL = 'normas'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def prediccion():
    """Casilla para repartir fichas de una predicción: un número entre 0 y 10."""
    return models.IntegerField(min=0, max=10, blank=True)

def calificacion():
    """Calificación KW de un reparto: categoría de la escala (1 = muy inapropiado)."""
    return models.IntegerField(widget=widgets.RadioSelectHorizontal, blank=True)


def valor_numerico():
    """Valor numérico de una calificación KW, entre -1 y 1."""
    return models.FloatField(blank=True)

class Player(BasePlayer):
    # Método BX: creencia normativa personal
    bx_norma_personal = models.IntegerField(
        label='En tu opinión, ¿cuál de estos repartos es el apropiado en esta situación?',
        widget=widgets.RadioSelect,
    )
    bx_personal_segundos = models.IntegerField(blank=True)

    # Método BX: control de comprensión 2
    control2_bx = models.IntegerField(
        label='En la siguiente pantalla vas a repartir 10 fichas. ¿Qué tienes que predecir?',
        choices=[
            [1, 'Qué reparto me parece apropiado a mí'],
            [2, 'Qué reparto elegirán los demás cuando decidan de verdad'],
            [3, 'Cuántos participantes eligieron cada reparto como el apropiado'],
        ],
        widget=widgets.RadioSelect,
    )
    control2_intentos = models.IntegerField(initial=0)

    # Método BX: expectativa normativa (predicción de lo que respondieron los demás)
    bx_pred_1 = prediccion()
    bx_pred_2 = prediccion()
    bx_pred_3 = prediccion()
    bx_pred_4 = prediccion()
    bx_pred_5 = prediccion()
    bx_moda_predicha = models.IntegerField(blank=True)
    bx_segundos = models.IntegerField(blank=True)

    # Expectativas empíricas: una casilla por reparto (hasta 5 repartos)
    ee_1 = prediccion()
    ee_2 = prediccion()
    ee_3 = prediccion()
    ee_4 = prediccion()
    ee_5 = prediccion()
    ee_segundos = models.IntegerField(blank=True)

        # Método KW: control de comprensión 2
    control2_kw = models.IntegerField(
        label='En la siguiente pantalla vas a calificar cada reparto. '
              'Para esta actividad, ¿qué significa que un reparto sea "apropiado"?',
        choices=[
            [1, 'Que yo lo elegiría si estuviera en esa situación'],
            [2, 'Que la mayoría de la gente lo consideraría correcto o aceptable'],
            [3, 'Que la mayoría de la gente lo elegiría si estuviera en esa situación'],
        ],
        widget=widgets.RadioSelect,
    )

    # Método KW: calificación de cada reparto (categoría y valor numérico)
    kw_calif_1 = calificacion()
    kw_calif_2 = calificacion()
    kw_calif_3 = calificacion()
    kw_calif_4 = calificacion()
    kw_calif_5 = calificacion()
    kw_calif_1_num = valor_numerico()
    kw_calif_2_num = valor_numerico()
    kw_calif_3_num = valor_numerico()
    kw_calif_4_num = valor_numerico()
    kw_calif_5_num = valor_numerico()
    kw_segundos = models.IntegerField(blank=True)

    decision = models.IntegerField(
        label='¿Qué reparto eliges?',
        widget=widgets.RadioSelect,
    )
    decision_segundos = models.IntegerField(blank=True)


# FUNCIONES

def participa(player: Player):
    """True si el participante aceptó participar."""
    return player.participant.consentimiento


def opciones_reparto(player: Player):
    """Lista de opciones (número, texto) en el formato 'quedarse con X y dar Y'."""
    config = player.session.config
    etiqueta = config['etiqueta_moneda']
    return [
        (i, f'Quedarse con {queda} {etiqueta} y dar {da} {etiqueta}')
        for i, (queda, da) in enumerate(leer_repartos(config), start=1)
    ]


def decision_choices(player: Player):
    return opciones_reparto(player)



def bx_norma_personal_choices(player: Player):
    return opciones_reparto(player)

def opciones_escala(player: Player):
    """Opciones de la escala KW: (1, 'Muy inapropiado'), (2, ...), ..."""
    etiquetas = ESCALAS_KW[player.session.config['categorias_kw']]
    return list(enumerate(etiquetas, start=1))


def kw_calif_1_choices(player: Player):
    return opciones_escala(player)


def kw_calif_2_choices(player: Player):
    return opciones_escala(player)


def kw_calif_3_choices(player: Player):
    return opciones_escala(player)


def kw_calif_4_choices(player: Player):
    return opciones_escala(player)


def kw_calif_5_choices(player: Player):
    return opciones_escala(player)


def kw_en_posicion(player: Player, momento, posicion):
    """
    True si las pantallas de KW van aquí para este participante.
    momento: 'antes' o 'despues' de la decisión.
    posicion: 'primero' (antes de BX) o 'segundo' (después de BX).
    Si solo le toca KW, sus pantallas van en la posición 'primero'.
    """
    if not (bloque_norma_aqui(player, momento) and usa_metodo(player, 'kw')):
        return False
    kw_va_primero = player.participant.metodo == 'kw' or player.participant.orden_metodo == 'kw_bx'
    return kw_va_primero == (posicion == 'primero')

def moda_predicha(player: Player, prefijo):
    """
    Número del reparto con más fichas en una predicción.
    Si hay empate en el máximo, devuelve None (vacío), como pide el apartado 6.3.
    """
    campos = campos_prediccion(player, prefijo)
    fichas = [getattr(player, campo) for campo in campos]
    maximo = max(fichas)
    if fichas.count(maximo) > 1:
        return None
    return fichas.index(maximo) + 1

def usa_metodo(player: Player, metodo):
    """True si al participante le toca el método indicado ('bx' o 'kw')."""
    return player.participant.metodo in [metodo, 'ambos']


def bloque_norma_aqui(player: Player, momento):
    """
    True si el bloque de creencias (norma y expectativas) va en este momento
    para el participante: 'antes' o 'despues' de la decisión.
    """
    if not participa(player):
        return False
    if momento == 'antes':
        return player.participant.orden_bloques == 'norma_primero'
    return player.participant.orden_bloques == 'decision_primero'

def campos_prediccion(player: Player, prefijo):
    """Nombres de las casillas que se usan según el número de repartos: ee_1, ee_2..."""
    n = len(leer_repartos(player.session.config))
    return [f'{prefijo}_{i}' for i in range(1, n + 1)]

def comprobar_suma_10(values, campos):
    """Mensaje de error si las fichas no suman exactamente 10; None si están bien."""
    if any(values[campo] is None for campo in campos):
        return 'Escribe un número en todas las casillas (puede ser 0).'
    total = sum(values[campo] for campo in campos)
    if total < 10:
        faltan = 10 - total
        verbo = 'falta' if faltan == 1 else 'faltan'
        return f'Las fichas tienen que sumar exactamente 10. Te {verbo} {faltan}.'
    if total > 10:
        sobran = total - 10
        verbo = 'sobra' if sobran == 1 else 'sobran'
        return f'Las fichas tienen que sumar exactamente 10. Te {verbo} {sobran}.'
    return None


# PÁGINAS


class BXPersonal(Page):
    form_model = 'player'
    form_fields = ['bx_norma_personal']
    template_name = 'normas/BXPersonal.html'

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'bx_personal')
        return dict(opciones=[texto for numero, texto in opciones_reparto(player)])

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.bx_personal_segundos = segundos_transcurridos(player, 'bx_personal')

class Control2BX(Page):
    form_model = 'player'
    form_fields = ['control2_bx']
    template_name = 'normas/Control2BX.html'

    @staticmethod
    def error_message(player: Player, values):
        player.control2_intentos += 1
        if not player.session.config['exigir_controles']:
            return None
        if values['control2_bx'] != 3:
            return dict(control2_bx='Esta respuesta no es correcta. Vuelve a intentarlo.')


class BXPrediccion(Page):
    form_model = 'player'
    template_name = 'normas/BXPrediccion.html'

    @staticmethod
    def get_form_fields(player: Player):
        return campos_prediccion(player, 'bx_pred')

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'bx_prediccion')
        campos = campos_prediccion(player, 'bx_pred')
        textos = [texto for numero, texto in opciones_reparto(player)]
        return dict(filas=list(zip(campos, textos)))

    @staticmethod
    def error_message(player: Player, values):
        return comprobar_suma_10(values, campos_prediccion(player, 'bx_pred'))

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.bx_segundos = segundos_transcurridos(player, 'bx_prediccion')
        player.bx_moda_predicha = moda_predicha(player, 'bx_pred')

class Control2KW(Page):
    form_model = 'player'
    form_fields = ['control2_kw']
    template_name = 'normas/Control2KW.html'

    @staticmethod
    def error_message(player: Player, values):
        player.control2_intentos += 1
        if not player.session.config['exigir_controles']:
            return None
        if values['control2_kw'] != 2:
            return dict(control2_kw='Esta respuesta no es correcta. Vuelve a intentarlo.')


class KWCalificacion(Page):
    form_model = 'player'
    template_name = 'normas/KWCalificacion.html'

    @staticmethod
    def get_form_fields(player: Player):
        return campos_prediccion(player, 'kw_calif')

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'kw_calificacion')
        campos = campos_prediccion(player, 'kw_calif')
        textos = [texto for numero, texto in opciones_reparto(player)]
        etiquetas = [e.lower() for e in ESCALAS_KW[player.session.config['categorias_kw']]]
        return dict(
            filas=list(zip(campos, textos)),
            opciones=textos,
            escala_texto=', '.join(etiquetas[:-1]) + ' o ' + etiquetas[-1],
        )

    @staticmethod
    def error_message(player: Player, values):
        campos = campos_prediccion(player, 'kw_calif')
        if any(values[campo] is None for campo in campos):
            return 'Califica todos los repartos antes de continuar.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.kw_segundos = segundos_transcurridos(player, 'kw_calificacion')
        k = player.session.config['categorias_kw']
        for campo in campos_prediccion(player, 'kw_calif'):
            categoria = getattr(player, campo)
            setattr(player, campo + '_num', valor_kw(categoria, k))

class Control2KWAntesPrimero(Control2KW):
    @staticmethod
    def is_displayed(player: Player):
        return kw_en_posicion(player, 'antes', 'primero')


class KWCalificacionAntesPrimero(KWCalificacion):
    @staticmethod
    def is_displayed(player: Player):
        return kw_en_posicion(player, 'antes', 'primero')


class Control2KWAntesSegundo(Control2KW):
    @staticmethod
    def is_displayed(player: Player):
        return kw_en_posicion(player, 'antes', 'segundo')


class KWCalificacionAntesSegundo(KWCalificacion):
    @staticmethod
    def is_displayed(player: Player):
        return kw_en_posicion(player, 'antes', 'segundo')


class Control2KWDespuesPrimero(Control2KW):
    @staticmethod
    def is_displayed(player: Player):
        return kw_en_posicion(player, 'despues', 'primero')


class KWCalificacionDespuesPrimero(KWCalificacion):
    @staticmethod
    def is_displayed(player: Player):
        return kw_en_posicion(player, 'despues', 'primero')


class Control2KWDespuesSegundo(Control2KW):
    @staticmethod
    def is_displayed(player: Player):
        return kw_en_posicion(player, 'despues', 'segundo')


class KWCalificacionDespuesSegundo(KWCalificacion):
    @staticmethod
    def is_displayed(player: Player):
        return kw_en_posicion(player, 'despues', 'segundo')

class BXPersonalAntes(BXPersonal):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'antes') and usa_metodo(player, 'bx')


class BXPersonalDespues(BXPersonal):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'despues') and usa_metodo(player, 'bx')

class Expectativas(Page):
    form_model = 'player'
    template_name = 'normas/Expectativas.html'

    @staticmethod
    def get_form_fields(player: Player):
        return campos_prediccion(player, 'ee')

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'expectativas')
        campos = campos_prediccion(player, 'ee')
        textos = [texto for numero, texto in opciones_reparto(player)]
        return dict(filas=list(zip(campos, textos)))

    @staticmethod
    def error_message(player: Player, values):
        return comprobar_suma_10(values, campos_prediccion(player, 'ee'))

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.ee_segundos = segundos_transcurridos(player, 'expectativas')

class Control2BXAntes(Control2BX):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'antes') and usa_metodo(player, 'bx')


class Control2BXDespues(Control2BX):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'despues') and usa_metodo(player, 'bx')


class BXPrediccionAntes(BXPrediccion):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'antes') and usa_metodo(player, 'bx')


class BXPrediccionDespues(BXPrediccion):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'despues') and usa_metodo(player, 'bx')

class ExpectativasAntes(Expectativas):
    """Expectativas cuando la norma se mide antes de decidir."""
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'antes')


class ExpectativasDespues(Expectativas):
    """Expectativas cuando la norma se mide después de decidir."""
    @staticmethod
    def is_displayed(player: Player):
        return bloque_norma_aqui(player, 'despues')

class Decision(Page):
    form_model = 'player'
    form_fields = ['decision']

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'decision')
        return dict()

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.decision_segundos = segundos_transcurridos(player, 'decision')


page_sequence = [
    # Bloque de creencias, si va antes de la decisión
    Control2KWAntesPrimero,
    KWCalificacionAntesPrimero,
    BXPersonalAntes,
    Control2BXAntes,
    BXPrediccionAntes,
    Control2KWAntesSegundo,
    KWCalificacionAntesSegundo,
    ExpectativasAntes,
    # Decisión real
    Decision,
    # Bloque de creencias, si va después de la decisión
    Control2KWDespuesPrimero,
    KWCalificacionDespuesPrimero,
    BXPersonalDespues,
    Control2BXDespues,
    BXPrediccionDespues,
    Control2KWDespuesSegundo,
    KWCalificacionDespuesSegundo,
    ExpectativasDespues,
]