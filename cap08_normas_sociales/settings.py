from os import environ

SESSION_CONFIGS = [
    dict(
        name='normas_sociales',
        display_name='Normas sociales',
        doc="""
        <b>Valores posibles de los parámetros</b> (escríbelos exactamente así, sin tildes):<br>
        <b>incentivos:</b> hipotetico · puntos · monetario<br>
        <b>marco:</b> ganada · asignada · aleatorio<br>
        <b>metodo:</b> bx · kw · ambos · aleatorio<br>
        <b>orden_metodo:</b> bx_kw · kw_bx · aleatorio (solo cuenta si metodo = ambos)<br>
        <b>orden_bloques:</b> norma_primero · decision_primero · aleatorio<br>
        <b>semilla:</b> 0 para un sorteo distinto cada vez, u otro número para repetir el mismo sorteo<br>
        <b>tarea_esfuerzo:</b> cuestionario<br>
        <b>repartos:</b> entre 2 y 5 opciones separadas por |, cada una como "se queda:da",
        sumando la dotación. Ejemplo: 20:80|45:55|80:20<br>
        """,
        app_sequence=['intro', 'dotacion', 'normas', 'cierre'],
        num_demo_participants=4,
        incentivos='puntos',
        etiqueta_moneda='fichas',
        moneda_local='COP',
        tasa_cambio=1000,
        dotacion=100,
        prob_pago=10,
        exigir_controles=True,
        marco='aleatorio',
        metodo='aleatorio',
        orden_metodo='aleatorio',
        orden_bloques='norma_primero',
        semilla=0,
        tarea_esfuerzo='cuestionario',
        umbral_tarea=3,
        repartos='20:80|45:55|80:20',
        pago_bx=20,
        pago_kw=20,
        categorias_kw=4,
        pago_ee=20,
        tolerancia_prediccion=1,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = ['consentimiento', 'marco', 'metodo', 'orden_metodo', 'orden_bloques']
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'es'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'COP'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '5116585859095'
