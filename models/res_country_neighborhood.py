# coding: utf-8
from odoo import _, api, fields, models


class ResCountryNeighborhood(models.Model):
    _name = 'res.country.neighborhood'
    _description = 'Country/County/District/Neighborhood'

    code = fields.Char(
        required=True,
    )
    name = fields.Char(
        required=True,
    )
    district_id = fields.Many2one(
        comodel_name="res.country.district",
        required=True,
    )
