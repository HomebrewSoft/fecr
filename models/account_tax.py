# coding: utf-8
from odoo import _, api, fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    code = fields.Char(
        size=4,
        required=True,
        default='1',
    )
    rate_code = fields.Selection(
        required=True,
        selection=[
            ('01', '0%'),
            ('02', '1%'),
            ('03', '2%'),
            ('04', '4%'),
            ('05', 'Transitorio 0%'),
            ('06', 'Transitorio 4%'),
            ('07', 'Transitorio 8%'),
            ('08', '13%'),
        ]
    )
