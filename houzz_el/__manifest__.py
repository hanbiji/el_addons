{
    'name': 'Houzz Eileen',
    'description': 'Houzz API.',
    'author': 'Joe Han',
    'depends': ['sale'],
    'application': True,
    'data': [
        'views/houzz_menu.xml',
        'views/houzz_view.xml',
        'views/sale_view.xml',
        'views/sale_order_tree.xml',
        'wizard/houzz_order_import_view.xml',
        'wizard/houzz_stock_view.xml',

        'security/ir.model.access.csv'
    ]
}