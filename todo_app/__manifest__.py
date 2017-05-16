{
    'name': 'To-Do Application',
    'summary': 'To-Do Tasks',
    'version': '1.6.3',
    'author': 'Joe Han',
    'depends': ['base', 'mail'],
    'application': True,
    'website': 'http://www.wiisoft.com',
    'data': [
        'security/ir.model.access.csv',
        'security/todo_access_rules.xml',
        'views/todo_menu.xml', 
        'views/todo_view.xml'
    ]
}