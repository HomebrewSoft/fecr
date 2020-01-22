# coding: utf-8
import http.client
import json
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ElectronicInvoice(models.AbstractModel):
    _name = 'electronic_invoice'
    _description = 'Electronic Invoice'

    # Header
    doc_type = fields.Selection(
        required=True,
        selection=[
            ('01', 'Factura'),
            ('04', 'Tiquete Electrónico'),
            ('09', 'Factura Electrónica de Exportación'),
        ]
    )
    activity_id = fields.Many2one(
        comodel_name='res.company.activity',
        default=lambda self: self.env['res.company']._company_default_get('account.invoice').default_activity_id,
        required=True,
    )
    emission_date = fields.Date(
        required=True,
    )
    sale_condition = fields.Selection(
        required=True,
        selection=[
            ('01', 'Contado'),
            ('02', 'Crédito'),
            ('03', 'Consignación'),
            ('04', 'Apartado'),
            ('05', 'Arrendamiento Opción Compra'),
            ('06', 'Arrendamiento Función Financiera'),
            ('99', 'Otros'),
        ]
    )
    payment_method = fields.Selection(
        required=True,
        selection=[
            ('01', 'Efectivo'),
            ('02', 'Tarjeta'),
            ('03', 'Cheque'),
            ('04', 'Transferencia'),
            ('05', 'Recaudado terceros'),
            ('99', 'Otros'),
        ]
    )
    # API
    sequence = fields.Char(
        copy=False,
        readonly=True,
    )
    key = fields.Char(
        copy=False,
        readonly=True,
    )
    electronic_invoice_xml = fields.Binary(
        attachment=True,
        copy=False,
        readonly=True,
        string='XML'
    )
    fname_electronic_invoice_xml = fields.Char(
        compute='_get_fname_electronic_invoice_xml'
    )
    electronic_invoice_xml_signed = fields.Binary(
        attachment=True,
        copy=False,
        readonly=True,
        string='XML Signed'
    )
    fname_electronic_invoice_xml_signed = fields.Char(
        compute='_get_fname_electronic_invoice_xml_signed'
    )
    ei_response_code = fields.Char(
        copy=False,
        readonly=True,
        string='Response Code'
    )
    ei_status_code = fields.Char(
        copy=False,
        readonly=True,
        string='Status Code'
    )
    ei_status_desc = fields.Char(
        copy=False,
        readonly=True,
        string='EI Status'
    )
    ei_message = fields.Char(
        copy=False,
        readonly=True,
        string='Message'
    )
    ei_message_response = fields.Char(
        copy=False,
        readonly=True,
        string='Response'
    )
    ei_date = fields.Char(
        copy=False,
        readonly=True,
        string='Date'
    )

    @api.depends('number', 'electronic_invoice_xml')
    def _get_fname_electronic_invoice_xml(self):
        for record in self:
            if record.electronic_invoice_xml:
                if record.number:
                    record.fname_electronic_invoice_xml = '{}.xml'.format(record.number)
                else:
                    record.fname_electronic_invoice_xml = '{} {}.xml'.format(record.partner_id.vat, record.date_invoice)

    @api.depends('number', 'electronic_invoice_xml_signed')
    def _get_fname_electronic_invoice_xml_signed(self):
        for record in self:
            if record.electronic_invoice_xml_signed:
                if record.number:
                    record.fname_electronic_invoice_xml_signed = '{}.xml'.format(record.number)
                else:
                    record.fname_electronic_invoice_xml_signed = '{} {}.xml'.format(record.partner_id.vat, record.date_invoice)

    def _get_header(self):
        header = {
            'TipoDocumento': self.doc_type,
            # 'SecuenciaControlada': 0,
            # 'NumeroConsecutivo': 0,
            # 'Clave': 0,
            # 'SecuenciaDocumento': 0,
            'Sucursal': 1,  # TODO Check
            'Terminal': 1,  # TODO Check
            'CodigoActividad': self.activity_id.code,
            'FechaEmision': fields.Date.to_string(self.emission_date),
            'Receptor': {
                'Nombre': self.partner_id.name,
                'IdentificacionTipo': self.partner_id.identification_type,
                'IdentificacionNumero': self.partner_id.vat,
                'NombreComercial': self.partner_id.name,
                'UbicacionProvincia': self.partner_id.state_id.code,
                'UbicacionCanton': self.partner_id.county_id.code,
                'UbicacionBarrio': self.partner_id.neighborhood_id.code,
                'UbicacionOtrasSenas': self.partner_id.street,
                # 'TelefonoArea': ,
                'TelefonoNumero': int(''.join(d for d in self.partner_id.phone if d.isdigit())),
                'CorreoElectronico': self.partner_id.email,
                'CorreoElectronicoCC': self.partner_id.invoices_email or '',
                # 'FaxArea': ,
                # 'FaxNumero': ,
            },
            'CondicionVenta': self.sale_condition,
            # 'PlazoCredito': ,  # TODO?
            'MedioPago': [int(self.payment_method)],
            'TipoCambio': 1.0,  # TODO?
            'CodigoMoneda': 1,  # TODO?
        }
        return header

    def _get_details(self):
        details = []
        for line in self.invoice_line_ids:
            taxes = sum(line.invoice_line_tax_ids.mapped('amount'))
            details.append({
                'EsServicio': 'S' if line.product_id.type == 'service' else 'N',
                'Codigo': [line.product_id.default_code],
                # 'PartidaArancelaria': ,  # TODO?
                'Cantidad': line.quantity,
                'UnidadMedida': line.product_id.uom_id.code,
                'UnidadMedidaComercial': line.product_id.uom_id.code,
                'Detalle': line.product_id.name,
                'PrecioUnitario': line.price_unit,
                # 'Descuento': ,
                'DescuentoUnitario': line.discount * line.price_unit,
                # 'BaseImponible': ,
                'BaseImponibleUnitario': taxes * line.price_unit,
                'Impuestos': [{
                    'Codigo': tax.code,
                    'CodigoTarifa': tax.rate_code,
                    'Tarifa': tax.amount,
                    # 'Exoneracion': ,  # TODO?
                } for tax in line.invoice_line_tax_ids]
            })
        return details

    def _get_doc(self):
        doc = {
            'Encabezado': self._get_header(),
            'LineasDetalle': self._get_details(),
            # 'InformacionReferencia': ,  # TODO?
        }
        return doc

    @api.multi
    def send_json(self):
        # TODO checks
        conn = http.client.HTTPSConnection(self.company_id.ei_url_api)
        body = {
            'CodigoCliente': self.company_id.ei_id_user,
            'DocElectronicos': [
                self._get_doc(),
            ],
        }
        headers = {
            'Content-Type': 'application/json',
            'Usuario': self.company_id.ei_user,
            'UsuarioClave': self.company_id.ei_password,
            'CodigoCliente': self.company_id.ei_id_user,
        }
        _logger.info('Sending JSON %s', body)
        try:
            conn.request("POST", self.company_id.ei_service_document_register, json.dumps(body), headers)
            response = conn.getresponse()
            response = response.read()
            response = response.decode('utf-8')
            _logger.info('Response %s', response)
            response = json.loads(response)
        except:
            self.ei_response_code = '-1'
            self.ei_message = 'Error sending the JSON'
            self.ei_date = fields.Date.to_string(fields.Date.today())
        else:
            self.ei_response_code = response['CodigoRespuesta']
            self.ei_message = response['Mensaje']
            self.ei_date = response['Fecha']
            if self.ei_response_code == '1':
                _logger.info('Response {}'.format(response['Id']))
                self.sequence = response['NumeroConsecutivo']
                self.key = response['Clave']
                self.action_invoice_open()
            return response

    @api.multi
    def query(self):
        conn = http.client.HTTPSConnection(self.company_id.ei_url_api)
        # TODO checks
        headers = {
            'Usuario': self.company_id.ei_user,
            'UsuarioClave': self.company_id.ei_password,
            'CodigoCliente': self.company_id.ei_id_user,
            'NumeroConsecutivo': self.sequence,
            'Clave': self.key,
        }
        _logger.info('Making query to sequence: {} key: {}'.format(self.sequence, self.key))
        conn.request("POST", self.company_id.ei_service_document_query, '', headers)
        response = json.loads(conn.getresponse().read().decode("utf-8"))
        self.ei_response_code = response['CodigoRespuesta']
        self.ei_message = response['Mensaje']
        self.ei_date = response['Fecha']
        if self.ei_response_code == '1':
            _logger.info('Response {}'.format(response['Id']))
            self.ei_status_code = response['CodigoEstado']
            self.ei_status_desc = response['DescripcionEstado']
            self.ei_message_response = response['MensajeRespuesta']
            self.electronic_invoice_xml_signed = response['XMLFirmado']
            self.electronic_invoice_xml = response['XMLRespuesta']
        return response
