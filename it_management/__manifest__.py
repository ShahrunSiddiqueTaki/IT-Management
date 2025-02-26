# -*- coding: utf-8 -*-

{
    'name': 'IT Management',
    'category': 'IT/',
    'sequence': 0,
    'summary': 'IT Requisition',
    'description': """""",
    'depends': ['base', 'mail', 'stock', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/res_lang_data.xml',
        'data/report_paperfomat.xml',
        'report/requisition_report.xml',
        'views/it_requisition_views.xml',
    ],
    'demo': [],
    'application': True,
    'license': 'LGPL-3',
    'assets': {}
}
