{
    'name': 'Walmart Eileen',
    'description': 'Walmart Order Manage.',
    'author': 'Joe Han',
    'depends': ['sale'],
    'application': True,
    'data': [
        'security/ir.model.access.csv',
        'views/walmart_menu.xml',
        'views/walmart_view.xml',
        'views/sale_view.xml',
        'views/sale_order_tree.xml',
        'wizard/walmart_order_import_view.xml'
    ]
}