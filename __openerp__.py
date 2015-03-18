{
    'name': 'copia_delivery_routing',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Routing for Copia(Kenya) Delivery Order',
    'description': """
      Routing with auto generated sequence for Delivery notes, Pick list and Invoices to describe the route,driver and agents.
    """,
    'author': 'Revathi',
    'website': '',
    'depends': ["base","stock","account"],
    'data': [
            'delivery_routing_view.xml',
            'security/ir.model.access.csv',

    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    
}
