from os import environ

SESSION_CONFIGS = [
    dict(
        name='deshonestidad',
        display_name='Deshonestidad: declaración de ingresos',
        doc="""
        <b>Valores posibles de los parámetros</b> (escríbelos exactamente así, sin tildes):<br>
        <b>incentivos:</b> hipotetico · puntos · monetario<br>
        <b>tratamiento:</b> aleatorio · control · sin_explicacion · inversion · salarios
        (con aleatorio, cada grupo recibe uno, repartidos de forma equilibrada)<br>
        <b>Impuesto:</b> en control se cobra impuesto_fondo + impuesto_admin; en los demás
        tratamientos se cobra impuesto_total, que tiene que ser igual a
        impuesto_fondo + impuesto_admin + impuesto_extra. Todo en porcentaje.<br>
        <b>prob_auditoria y multa:</b> en porcentaje. La multa se calcula sobre el ingreso no declarado.<br>
        <b>semilla:</b> 0 para un sorteo distinto cada vez, u otro número para repetir el mismo sorteo
        """,
        app_sequence=['intro', 'tarea_ingreso', 'declaracion', 'cierre'],
        num_demo_participants=4,

        # Pagos
        incentivos='puntos',
        etiqueta_moneda='puntos',
        moneda_local='COP',
        tasa_cambio=100,
        prob_pago=10,

        # Grupos y rondas
        tamano_grupo=4,
        num_rondas=10,

        # Tarea de ingreso
        segundos_tarea=30,
        puntos_por_acierto=10,

        # Impuesto y tratamientos
        tratamiento='aleatorio',
        impuesto_total=40,
        impuesto_fondo=25,
        impuesto_admin=5,
        impuesto_extra=10,

        # Auditoría, fondo e información
        prob_auditoria=10,
        multa=40,
        multiplicador=2,
        info_social=False,

        # Operativa del aula
        exigir_controles=True,
        semilla=0,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = [
    'consentimiento',
    'en_juego',
    'tratamiento',
    'ingreso',
]
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'es'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '2872454464702'
