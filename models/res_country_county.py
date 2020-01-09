# coding: utf-8
from odoo import _, api, fields, models


class ResCountryCounty(models.Model):
    _name = 'res.country.county'
    _description = 'Country/County'

    code = fields.Char(
        required=True,
    )
    name = fields.Char(
        required=True,
    )
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        required=True,
    )
