# -*- encoding: utf-8 -*-
{
    'name': u'订单退款',
    'summary': u'订单退款操作',
    'author': 'Joe Han',
    'depends': ['base', 'product', 'sale', 'mail'],
    'application': True,
    'website': 'http://www.wiisoft.com',
    'data': [
        'views/view.xml',
        'security/ir.model.access.csv'
    ]
}