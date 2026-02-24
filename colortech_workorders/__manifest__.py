{
    'name': 'ColorTech - Órdenes de Trabajo',
    'version': '19.0.1.0.0',
    'summary': 'Gestión de órdenes de trabajo para personalización de dispositivos',
    'description': """
        Módulo personalizado para ColorTech Guadalajara S.L.
        =====================================================

        Gestiona las órdenes de trabajo del taller de pintura y
        personalización de dispositivos electrónicos:

        - Registro de dispositivos de clientes
        - Catálogo de servicios con tarifas
        - Órdenes de trabajo con flujo de estados
        - Asignación de técnicos
        - Control de tiempos y costes
        - Tipos de dispositivos configurables
    """,
    'author': 'ColorTech Guadalajara S.L.',
    'website': 'https://www.colortech-guadalajara.es',
    'category': 'Services',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/colortech_device_type_views.xml',
        'views/colortech_service_views.xml',
        'views/colortech_workorder_views.xml',
        'views/colortech_menus.xml',
        'data/colortech_demo_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
