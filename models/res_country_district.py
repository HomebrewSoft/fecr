# coding: utf-8
from odoo import _, api, fields, models


class ResCountryDistrict(models.Model):
    _name = 'res.country.district'
    _description = 'Country/County/District'

    code = fields.Char(
        required=True,
    )
    name = fields.Char(
        required=True,
    )
    county_id = fields.Many2one(
        comodel_name="res.country.county",
        required=True,
    )
