from otree.api import *
import random
from utilidades import iniciar_cronometro, segundos_transcurridos, error_entero, rango

doc = """
Capítulo 9. Preferencias intergrupales. App 3: reparto entre otras dos personas.
Escenario 1 (basado en Chen y Li, 2009). El participante reparte la dotación entre otras
dos personas en tres situaciones (las dos de su propio grupo, las dos del otro grupo,
una de cada uno), una por pantalla y en orden aleatorio. Él no recibe nada del reparto.
"""


class C(BaseConstants):
    NAME_IN_URL = 'espectador'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    SITUACIONES = ['propio_propio', 'otro_otro', 'mixto']


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def monto():
    """Casilla de reparto. blank=True para mostrar nuestros propios mensajes de error."""
    return models.IntegerField(label='', min=None, blank=True)

class Player(BasePlayer):
    # Orden de las situaciones, por ejemplo 'mixto|propio_propio|otro_otro'
    espectador_orden = models.StringField()
    # En la situación mixta: qué casilla va primero
    espectador_orden_mixto = models.StringField()

    espectador_propio_propio_1 = monto()
    espectador_propio_propio_2 = monto()
    espectador_otro_otro_1 = monto()
    espectador_otro_otro_2 = monto()
    espectador_mixto_propio = monto()
    espectador_mixto_otro = monto()

    espectador_propio_propio_segundos = models.IntegerField(blank=True)
    espectador_otro_otro_segundos = models.IntegerField(blank=True)
    espectador_mixto_segundos = models.IntegerField(blank=True)


def creating_session(subsession: Subsession):
    """Sortea, para cada participante, el orden de las tres situaciones y el de la mixta."""
    semilla = subsession.session.config['semilla']
    # Se suma 1 para que este sorteo no repita el de la app intro cuando hay semilla
    azar = random.Random(semilla + 1) if semilla else random.Random()
    for player in subsession.get_players():
        orden = list(C.SITUACIONES)
        azar.shuffle(orden)
        player.espectador_orden = '|'.join(orden)
        player.espectador_orden_mixto = azar.choice(['propio_primero', 'otro_primero'])


# FUNCIONES

def participa(player: Player):
    return player.participant.consentimiento


def situacion(player: Player, k):
    """La situación que toca en la pantalla k (1 a 3), por ejemplo 'mixto'."""
    return player.espectador_orden.split('|')[k - 1]


def filas(player: Player, k):
    """Las dos casillas de la pantalla k, cada una con el texto que va a su lado."""
    caso = situacion(player, k)
    if caso == 'mixto':
        propio = dict(campo='espectador_mixto_propio', etiqueta='Persona de tu propio grupo')
        otro = dict(campo='espectador_mixto_otro', etiqueta='Persona del otro grupo')
        if player.espectador_orden_mixto == 'propio_primero':
            return [propio, otro]
        return [otro, propio]
    return [
        dict(campo=f'espectador_{caso}_1', etiqueta='Persona 1'),
        dict(campo=f'espectador_{caso}_2', etiqueta='Persona 2'),
    ]


def campos(player: Player, k):
    return [fila['campo'] for fila in filas(player, k)]


def datos_pantalla(player: Player, k):
    caso = situacion(player, k)
    iniciar_cronometro(player, f'espectador_{caso}')
    dotacion = player.session.config['dotacion_espectador']
    return dict(numero=k, caso=caso, filas=filas(player, k),
                rangos={campo: rango(0, dotacion, 'Completa este campo.')
                        for campo in campos(player, k)})

def errores_pantalla(player: Player, values, k):
    config = player.session.config
    dotacion = config['dotacion_espectador']
    errores = {}
    for campo in campos(player, k):
        error = error_entero(values[campo], 0, dotacion, 'Completa este campo.')
        if error:
            errores[campo] = error
    if errores:
        return errores
    if sum(values[campo] for campo in campos(player, k)) != dotacion:
        return (f'Los dos montos deben ser enteros y sumar exactamente {dotacion} '
                f'{config["etiqueta_moneda"]}.')


def guardar_tiempo(player: Player, k):
    caso = situacion(player, k)
    setattr(player, f'espectador_{caso}_segundos',
            segundos_transcurridos(player, f'espectador_{caso}'))


# PÁGINAS

class Introduccion(Page):
    @staticmethod
    def is_displayed(player: Player):
        return participa(player)


class Situacion(Page):
    """Base de las tres pantallas de reparto. Cada una solo cambia su número k."""
    form_model = 'player'
    template_name = 'espectador/Situacion.html'

    @staticmethod
    def is_displayed(player: Player):
        return participa(player)


class Situacion1(Situacion):
    @staticmethod
    def get_form_fields(player: Player):
        return campos(player, 1)

    @staticmethod
    def vars_for_template(player: Player):
        return datos_pantalla(player, 1)

    @staticmethod
    def error_message(player: Player, values):
        return errores_pantalla(player, values, 1)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        guardar_tiempo(player, 1)


class Situacion2(Situacion):
    @staticmethod
    def get_form_fields(player: Player):
        return campos(player, 2)

    @staticmethod
    def vars_for_template(player: Player):
        return datos_pantalla(player, 2)

    @staticmethod
    def error_message(player: Player, values):
        return errores_pantalla(player, values, 2)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        guardar_tiempo(player, 2)


class Situacion3(Situacion):
    @staticmethod
    def get_form_fields(player: Player):
        return campos(player, 3)

    @staticmethod
    def vars_for_template(player: Player):
        return datos_pantalla(player, 3)

    @staticmethod
    def error_message(player: Player, values):
        return errores_pantalla(player, values, 3)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        guardar_tiempo(player, 3)


page_sequence = [Introduccion, Situacion1, Situacion2, Situacion3]