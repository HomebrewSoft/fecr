# coding: utf-8
from odoo import _, api, fields, models


class ResCountryDistrict(models.Model):
    _inherit = 'code_name'
    _name = 'res.country.district'
    _description = 'Country/County/District'

    county_id = fields.Many2one(
        comodel_name="res.country.county",
        required=True,
    )
