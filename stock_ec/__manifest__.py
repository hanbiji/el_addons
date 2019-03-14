# -*- encoding: utf-8 -*-

{
    'name': '易仓系统海外仓，库存同步',
    'description': '易仓系统海外仓，库存同步',
    'author': 'Joe Han',
    'depends': ['stock', 'product'],
    'application': True,
    'data': [
        'views/ec_order_view.xml',
        'views/ec_config_view.xml',
        'views/stock_ec_menu.xml',
        'views/inherit_stock_picking.xml',
        'wizard/stock_ec_view.xml',
        'security/ir.model.access.csv'
    ]
}
