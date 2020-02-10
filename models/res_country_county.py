# coding: utf-8
from odoo import _, api, fields, models


class ResCountryCounty(models.Model):
    _inherit = 'code_name'
    _name = 'res.country.county'
    _description = 'Country/County'

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        required=True,
    )
