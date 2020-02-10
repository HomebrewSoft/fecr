# coding: utf-8
from odoo import _, api, fields, models


class ResCompanyActivity(models.Model):
    _inherit = 'code_name'
    _name = 'res.company.activity'
    _description = 'Company Economic Activity'

    description = fields.Char(
    )
    active = fields.Boolean(
        default=True,
    )
