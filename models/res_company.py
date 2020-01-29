# coding: utf-8
from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    ei_url_api = fields.Char(
        required=True,
        string='URL API'
    )
    ei_service_document_register = fields.Char(
        required=True,
        string='Service Document Register'
    )
    ei_service_document_query = fields.Char(
        required=True,
        string='Service Document Query'
    )
    ei_service_message_register = fields.Char(
        required=True,
        string='Service Message Register'
    )
    ei_user = fields.Char(
        required=True,
        string='User'
    )
    ei_password = fields.Char(
        required=True,
        string='Password'
    )
    ei_id_user = fields.Char(
        required=True,
        string='Id User'
    )
    ei_sucursal = fields.Integer(
        required=True,
        string='Sucursal',
    )
    ei_terminal = fields.Integer(
        required=True,
        string='Terminal',
    )
    ei_transmition_situation = fields.Integer(
        required=True,
        string='Transmition Situation',
    )
    default_activity_id = fields.Many2one(
        comodel_name='res.company.activity',
        ondelete='restrict',
    )
    activity_ids = fields.Many2many(
        comodel_name='res.company.activity',
        readonly=False,
    )
