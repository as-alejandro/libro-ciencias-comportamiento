from otree.api import *
import random


doc = """
Capítulo 10. Deshonestidad: declaración de ingresos. App 2: tarea de ingreso.
Contar cuántas veces aparece una figura en matrices de 6 × 4 durante segundos_tarea.
Cada acierto vale puntos_por_acierto. El ingreso se usa en todas las rondas.
"""


class C(BaseConstants):
    NAME_IN_URL = 'tarea_ingreso'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    FIGURAS = ['⬢', '⬟', '✚', '✦', '◧', '◪']
    FILAS = 4
    COLUMNAS = 6


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    tarea_aciertos = models.IntegerField(initial=0)
    tarea_intentos = models.IntegerField(initial=0)
    ingreso = models.IntegerField(blank=True)


# FUNCIONES

def participa(player: Player):
    """True si el participante aceptó participar."""
    return player.participant.consentimiento


def nuevo_ejercicio(player: Player):
    """Crea una matriz al azar, elige la figura que hay que contar y la guarda."""
    matriz = [[random.choice(C.FIGURAS) for _ in range(C.COLUMNAS)] for _ in range(C.FILAS)]
    objetivo = random.choice(C.FIGURAS)
    respuesta = sum(fila.count(objetivo) for fila in matriz)
    player.participant.vars['ejercicio'] = dict(matriz=matriz, objetivo=objetivo,
                                                respuesta=respuesta)
    return dict(matriz=matriz, objetivo=objetivo, numero=player.tarea_intentos + 1)


# PÁGINAS

class ExplicacionTarea(Page):
    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def vars_for_template(player: Player):
        puntos = player.session.config['puntos_por_acierto']
        return dict(ejemplo_ingreso=10 * puntos)


class Tarea(Page):
    @staticmethod
    def is_displayed(player: Player):
        return participa(player)

    @staticmethod
    def get_timeout_seconds(player: Player):
        return player.session.config['segundos_tarea']

    @staticmethod
    def js_vars(player: Player):
        # Si la persona recarga la página, sigue con el mismo ejercicio
        actual = player.participant.vars.get('ejercicio')
        if actual is None:
            return nuevo_ejercicio(player)
        return dict(matriz=actual['matriz'], objetivo=actual['objetivo'],
                    numero=player.tarea_intentos + 1)

    @staticmethod
    def live_method(player: Player, datos):
        """Recibe la respuesta de un ejercicio, la revisa y envía el siguiente."""
        try:
            respuesta = int(datos['respuesta'])
        except (KeyError, TypeError, ValueError):
            return
        player.tarea_intentos += 1
        if respuesta == player.participant.vars['ejercicio']['respuesta']:
            player.tarea_aciertos += 1
        return {player.id_in_group: nuevo_ejercicio(player)}

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.ingreso = player.tarea_aciertos * player.session.config['puntos_por_acierto']
        player.participant.ingreso = player.ingreso


class TuIngreso(Page):
    @staticmethod
    def is_displayed(player: Player):
        return participa(player)


page_sequence = [ExplicacionTarea, Tarea, TuIngreso]