from os import environ

SESSION_CONFIGS = [
    dict(
        name='preferencias_intergrupales',
        display_name='Preferencias intergrupales',
        doc="""
        <b>Valores posibles de los parámetros</b> (escríbelos exactamente así, sin tildes):<br>
        <b>niveles_confianza:</b> montos que puede enviar quien envía, separados por |, por ejemplo 0|25|50|75|100. El mayor tiene que ser igual a dotacion_confianza<br>        <b>nivel_referencia_creencias:</b> tiene que ser uno de los niveles anteriores<br>
        <b>orden_contraparte_dictador, orden_grupo_confianza, orden_grupo_creencias:</b>
        propio_primero · otro_primero · aleatorio<br>
        <b>orden_bloques_confianza:</b> emisor_primero · receptor_primero · aleatorio<br>
        <b>semilla:</b> 0 para un sorteo distinto cada vez, u otro número para repetir el mismo sorteo
        """,
        app_sequence=['intro', 'revelacion_grupo', 'espectador', 'dictador', 'confianza_estrategica', 'creencias', 'cierre'],
        num_demo_participants=4,

        # 2.1. Pagos (esta versión usa solo fichas)
        etiqueta_moneda='fichas',
        dotacion_espectador=100,
        dotacion_dictador=100,
        dotacion_confianza=100,
        multiplicador_confianza=3,
        niveles_confianza='0|25|50|75|100',
        nivel_referencia_creencias=100,
        premio_creencias=20,
        umbral_creencias=15,
        
        # 2.2. Diseño experimental
        orden_contraparte_dictador='aleatorio',
        orden_bloques_confianza='aleatorio',
        orden_grupo_confianza='aleatorio',
        orden_grupo_creencias='aleatorio',

        # 2.3. Operativa del aula
        exigir_controles=True,
        mostrar_resultados_aula=True,
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
    'grupo_asignado',
    'orden_contraparte_dictador',
    'orden_bloques_confianza',
    'orden_grupo_confianza',
    'orden_grupo_creencias',
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

SECRET_KEY = '5480477379543'
