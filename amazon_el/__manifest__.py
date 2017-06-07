# -*- encoding: utf-8 -*-
{
    'name': 'Amazon Eileen',
    'description': 'Amazon Order Manage.',
    'author': 'Joe Han',
    'depends': ['sale'],
    'application': True,
    'data': [
        'views/amazon_view.xml',
        'views/sale_view.xml',
        'views/sale_order_tree.xml',
        'wizard/amazon_order_import_view.xml',
        'views/feed_view.xml',
        'views/amazon_menu.xml',

        'security/ir.model.access.csv'
    ]
}