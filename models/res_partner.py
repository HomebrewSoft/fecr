# coding: utf-8
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    identification_type = fields.Selection(
        required=True,
        selection=[
            ('01', 'Fisico'),
            ('02', 'Juridico'),
            ('03', 'Dimex'),
            ('04', 'NITE'),
            ('10', 'Exrtanjero'),
        ]
    )
    county_id = fields.Many2one(
        comodel_name='res.country.county',
        ondelete='restrict',
    )
    district_id = fields.Many2one(
        comodel_name='res.country.district',
        ondelete='restrict',
    )
    neighborhood_id = fields.Many2one(
        comodel_name='res.country.neighborhood',
        ondelete='restrict',
    )
    invoices_email = fields.Char(
    )
    vat = fields.Char(
        required=True,
    )
