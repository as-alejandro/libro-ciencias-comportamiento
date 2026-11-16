from otree.api import *
from utilidades import iniciar_cronometro, segundos_transcurridos, leer_niveles


doc = """
Capítulo 9. Preferencias intergrupales. App 4: juego de confianza, método estratégico.
Cada participante responde como emisor (cuánto envía a alguien de su grupo y del
contrario) y como receptor (cuánto devuelve para cada monto y cada grupo del emisor).
Las casillas del receptor van numeradas por posición: la casilla 1 corresponde al primer
monto de 'niveles_enviado_confianza', la 2 al segundo, etc.
"""


class C(BaseConstants):
    NAME_IN_URL = 'confianza_estrategica'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def devolucion():
    """Casilla del receptor: cuánto devuelve en un caso concreto."""
    return models.IntegerField(min=0, blank=True)


class Player(BasePlayer):
    # Control de comprensión 3
    control3 = models.IntegerField(
        label='En las dos pantallas siguientes, ¿para qué casos tienes que responder?',
        choices=[
            [1, 'Solo para el caso que me vaya a tocar'],
            [2, 'Para todos los casos posibles, aunque al final solo se use uno de ellos'],
            [3, 'Solo para los casos en que la otra persona es de mi grupo'],
        ],
        widget=widgets.RadioSelect,
    )
    control3_intentos = models.IntegerField(initial=0)

    # Como emisor: cuánto envía según el grupo del receptor
    conf_emisor_propio = models.IntegerField(
        label='Si la otra persona es de tu mismo grupo, ¿cuánto le envías?', min=0,
    )
    conf_emisor_otro = models.IntegerField(
        label='Si la otra persona es del grupo contrario, ¿cuánto le envías?', min=0,
    )
    conf_emisor_segundos = models.IntegerField(blank=True)

    # Como receptor: cuánto devuelve para cada monto (casillas 1 a 11) y grupo del emisor
    conf_receptor_propio_1 = devolucion()
    conf_receptor_propio_2 = devolucion()
    conf_receptor_propio_3 = devolucion()
    conf_receptor_propio_4 = devolucion()
    conf_receptor_propio_5 = devolucion()
    conf_receptor_propio_6 = devolucion()
    conf_receptor_propio_7 = devolucion()
    conf_receptor_propio_8 = devolucion()
    conf_receptor_propio_9 = devolucion()
    conf_receptor_propio_10 = devolucion()
    conf_receptor_propio_11 = devolucion()
    conf_receptor_otro_1 = devolucion()
    conf_receptor_otro_2 = devolucion()
    conf_receptor_otro_3 = devolucion()
    conf_receptor_otro_4 = devolucion()
    conf_receptor_otro_5 = devolucion()
    conf_receptor_otro_6 = devolucion()
    conf_receptor_otro_7 = devolucion()
    conf_receptor_otro_8 = devolucion()
    conf_receptor_otro_9 = devolucion()
    conf_receptor_otro_10 = devolucion()
    conf_receptor_otro_11 = devolucion()
    conf_receptor_segundos = models.IntegerField(blank=True)


# FUNCIONES

def participa(player: Player):
    """True si el participante aceptó participar."""
    return player.participant.consentimiento


def conf_emisor_propio_max(player: Player):
    return player.session.config['dotacion_confianza']


def conf_emisor_otro_max(player: Player):
    return player.session.config['dotacion_confianza']


def grupos_en_orden(player: Player):
    """['propio', 'otro'] o ['otro', 'propio'], según orden_grupo_confianza."""
    if player.participant.orden_grupo_confianza == 'propio_primero':
        return ['propio', 'otro']
    return ['otro', 'propio']


def casillas_receptor(player: Player):
    """
    Una fila por monto: el monto enviado, lo que se recibe (ya multiplicado)
    y el nombre de las dos casillas, en el orden de grupos del participante.
    """
    config = player.session.config
    filas = []
    for i, nivel in enumerate(leer_niveles(config), start=1):
        filas.append(dict(
            enviado=nivel,
            recibido=nivel * config['multiplicador_confianza'],
            campos=[f'conf_receptor_{grupo}_{i}' for grupo in grupos_en_orden(player)],
        ))
    return filas


def bloque_aqui(player: Player, bloque, posicion):
    """
    True si el bloque ('emisor' o 'receptor') va en 'posicion' ('primero' o 'segundo')
    para este participante.
    """
    if not participa(player):
        return False
    primero = 'emisor' if player.participant.orden_bloques_confianza == 'emisor_primero' else 'receptor'
    if posicion == 'primero':
        return bloque == primero
    return bloque != primero


# PÁGINAS

class Control3(Page):
    form_model = 'player'
    form_fields = ['control3']

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def vars_for_template(player: Player):
        config = player.session.config
        return dict(maximo_recibido=config['dotacion_confianza'] * config['multiplicador_confianza'])

    @staticmethod
    def error_message(player: Player, values):
        player.control3_intentos += 1
        if not player.session.config['exigir_controles']:
            return None
        if values['control3'] != 2:
            return dict(control3='Esta respuesta no es correcta. Vuelve a intentarlo.')


class Emisor(Page):
    form_model = 'player'
    template_name = 'confianza_estrategica/Emisor.html'

    @staticmethod
    def get_form_fields(player: Player):
        return [f'conf_emisor_{grupo}' for grupo in grupos_en_orden(player)]

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'conf_emisor')
        return dict()

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.conf_emisor_segundos = segundos_transcurridos(player, 'conf_emisor')


class Receptor(Page):
    form_model = 'player'
    template_name = 'confianza_estrategica/Receptor.html'

    @staticmethod
    def get_form_fields(player: Player):
        return [campo for fila in casillas_receptor(player) for campo in fila['campos']]

    @staticmethod
    def vars_for_template(player: Player):
        iniciar_cronometro(player, 'conf_receptor')
        titulos = dict(propio='Si quien envía es de tu mismo grupo',
                       otro='Si quien envía es del grupo contrario')
        return dict(
            filas=casillas_receptor(player),
            columnas=[titulos[grupo] for grupo in grupos_en_orden(player)],
        )

    @staticmethod
    def error_message(player: Player, values):
        errores = {}
        for fila in casillas_receptor(player):
            for campo in fila['campos']:
                valor = values[campo]
                if valor is None:
                    errores[campo] = 'Escribe un número (puede ser 0).'
                elif valor > fila['recibido']:
                    errores[campo] = f'No puedes devolver más de {fila["recibido"]}.'
        return errores

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.conf_receptor_segundos = segundos_transcurridos(player, 'conf_receptor')


class EmisorPrimero(Emisor):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_aqui(player, 'emisor', 'primero')


class ReceptorPrimero(Receptor):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_aqui(player, 'receptor', 'primero')


class EmisorSegundo(Emisor):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_aqui(player, 'emisor', 'segundo')


class ReceptorSegundo(Receptor):
    @staticmethod
    def is_displayed(player: Player):
        return bloque_aqui(player, 'receptor', 'segundo')


page_sequence = [Control3, EmisorPrimero, ReceptorPrimero, EmisorSegundo, ReceptorSegundo]