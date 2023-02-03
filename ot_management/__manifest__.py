# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'OT Management',
    'version': '1.1',
    'category': 'Human Resources',
    'summary': 'Centralize employee information',
    'description': "",
    'website': 'https://www.odoo.com/page/employees',
    'images': [
    ],
    'depends': [
        'base_setup',
        'mail',
        'resource',
        'web',
        'hr',
        'project',
    ],
    'data': [
        'security/ot_security.xml',
        'security/ir.model.access.csv',

        # mail
        'data/mail_template.xml',
        'views/ot_registration_details.xml',
        'views/ot_request.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
    'license': 'LGPL-3',
}
