from os import environ

SESSION_CONFIGS = [
    dict(
        name='aversion_riesgo',
        display_name='Aversión al riesgo (Holt y Laury)',
        doc="""
        <b>Loterías</b> (en UME): la opción A paga a_alto o a_bajo; la opción B paga b_alto o b_bajo.
        En la decisión k, el pago alto tiene probabilidad k × 10 %.<br>
        <b>Práctica:</b> la opción X paga pract_x_1 o pract_x_2; la opción Y paga pract_y_1 o
        pract_y_2. El primer resultado tiene probabilidad pract_prob (%).<br>
        <b>en_laboratorio:</b> muestra las frases sobre levantar la mano.<br>
        <b>Pago:</b> real_world_currency_per_point = pesos por UME; participation_fee = pago fijo.
        """,
        app_sequence=['loterias'],
        num_demo_participants=1,

        # Loterías de la lista (UME)
        a_alto=200,
        a_bajo=160,
        b_alto=385,
        b_bajo=10,

        # Decisión de práctica (UME; no se paga)
        pract_prob=10,
        pract_x_1=100,
        pract_x_2=150,
        pract_y_1=50,
        pract_y_2=0,

        # Aula o laboratorio
        en_laboratorio=False,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=10.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'es'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'COP'
USE_POINTS = True
POINTS_CUSTOM_NAME = 'UME'

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '4791797837396'
