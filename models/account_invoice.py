# coding: utf-8
from odoo import _, api, fields, models


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'electronic_invoice']

    available_activity_ids = fields.Many2many(
        related='company_id.activity_ids',
    )
