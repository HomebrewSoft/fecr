# coding: utf-8
from odoo import _, api, fields, models


class AccountInvoiceDocType(models.Model):
    _inherit = 'code_name'
    _name = 'account.invoice.doc_type'
