{
    'name': 'SKU BOX',
    'summary': 'Team Sku box',
    'version': '1.3.3',
    'author': 'Joe Han',
    'depends': ['base', 'product', 'sale', 'mail'],
    'application': True,
    'website': 'http://www.wiisoft.com',
    'data': [
        'views/skubox_menu.xml',
        'views/skubox_view.xml',
        'security/ir.model.access.csv',
        'security/sku_access_rules.xml'
    ]
}