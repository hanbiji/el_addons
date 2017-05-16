{
    'name': 'Amazon Eileen',
    'description': 'Amazon Order Manage.',
    'author': 'Joe Han',
    'depends': ['sale'],
    'application': True,
    'data': [
        'security/ir.model.access.csv',
        'views/amazon_menu.xml',
        'views/amazon_view.xml',
        'views/sale_view.xml',
        'views/sale_order_tree.xml',
        'wizard/amazon_order_import_view.xml'
    ]
}