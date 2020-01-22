# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class UoMUoM(models.Model):
    _inherit = "uom.uom"
    code = fields.Char(
    )
