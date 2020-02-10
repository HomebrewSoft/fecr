# coding: utf-8
from odoo import _, api, fields, models


class ElectronicInvoiceDespatchType(models.AbstractModel):
    _name = 'code_name'
    _description = 'Basic Code/Desc Model'

    code = fields.Char(
        index=True,
    )
    name = fields.Char(
        index=True,
    )
