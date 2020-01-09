# coding: utf-8
from odoo import _, api, fields, models


class ResCompanyActivity(models.Model):
    _name = 'res.company.activity'
    _description = 'Company Economic Activity'

    name = fields.Char(
        required=True,
    )
    code = fields.Char(
        required=True,
    )
    description = fields.Char(
    )
    active = fields.Boolean(
        default=True,
    )
