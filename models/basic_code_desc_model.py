# coding: utf-8
from odoo import _, api, fields, models


class ElectronicInvoiceDespatchType(models.AbstractModel):
    _name = 'basic_code_desc_model'
    _description = 'Basic Code/Desc Model'

    code = fields.Char(
        required=True,
        index=True,
    )
    desc = fields.Char(
        required=True,
        index=True,
    )
    name = fields.Char(
        compute='_get_name',
        store=True,
        index=True,
    )

    @api.depends('code', 'desc')
    def _get_name(self):
        for record in self:
            record.name = u'{} - {}'.format(record.code, record.desc)
