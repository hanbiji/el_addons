{
    'name': 'Multiuser To-Do',
    'description': 'Extend the To-Do app to multiuser.',
    'author': 'Joe Han',
    'depends': ['todo_app', 'mail'],
    'data': 
    [
        'views/todo_task.xml',
        'security/todo_access_rules.xml'
    ],
    'demo':
    [
        'data/todo.task.csv',
        'data/todo_data.xml'
    ]
}