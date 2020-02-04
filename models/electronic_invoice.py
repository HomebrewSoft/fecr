# coding: utf-8
from base64 import b64decode
from datetime import datetime
from lxml import etree
import http.client
import json
import logging
import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def get(invoice, node):
    return invoice.xpath(node)[0].text


class ElectronicInvoice(models.AbstractModel):
    _name = 'electronic_invoice'
    _description = 'Electronic Invoice'

    # Header
    doc_type = fields.Selection(
        required=True,
        selection=[
            ('01', 'Factura Electrónica'),
            ('02', 'Nota de Débito'),
            ('03', 'Nota de Crédito'),
            ('04', 'Tiquete Electrónico'),
            ('05', 'Confirmacion comprobante electronico'),
            ('06', 'Confirmacion parcial comprobante electronico'),
            ('07', 'Rechazo comprobante electronico'),
            ('08', 'Factura Electrónica de Compra'),
            ('09', 'Factura Electrónica de Exportación'),
        ]
    )
    activity_id = fields.Many2one(
        comodel_name='res.company.activity',
        default=lambda self: self.env['res.company']._company_default_get('account.invoice').default_activity_id,
        required=True,
    )
    emission_date = fields.Datetime(
        readonly=True,
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
    electronic_invoice_pdf = fields.Char(
        copy=False,
        readonly=True,
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
    fname_xml_supplier_approval = fields.Char(
        attachment=True,
        copy=False,
    )
    xml_supplier_approval = fields.Binary(
        attachment=True,
        copy=False,
        string='XML Supplier',
    )
    ei_state = fields.Selection(
        [
            ('to_send', 'To Send'),
            ('to_query', 'To Query'),
            ('queried', 'Queried'),
        ],
        default='to_send',
        readonly=True,
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
            'Sucursal': self.company_id.ei_sucursal,
            'Terminal': self.company_id.ei_terminal,
            'SituacionEnvio': self.company_id.ei_transmition_situation,
            'CodigoActividad': self.activity_id.code,
            'FechaEmision': datetime.strftime(fields.Datetime.context_timestamp(self, self.emission_date), '%Y-%m-%dT%H:%M:%S'),
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
            # taxes = sum(line.invoice_line_tax_ids.mapped('amount')) / 100
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
                # 'BaseImponibleUnitario': taxes * line.price_unit,
                'Impuestos': [{
                    'Codigo': tax.code,
                    'CodigoTarifa': tax.rate_code,
                    'Tarifa': tax.amount,
                    # 'Exoneracion': ,  # TODO?
                } for tax in line.invoice_line_tax_ids]
            })
        return details

    def _get_doc(self):
        self.emission_date = fields.Datetime.now()
        doc = {
            'Encabezado': self._get_header(),
            'LineasDetalle': self._get_details(),
            # 'InformacionReferencia': ,  # TODO?
        }
        return doc

    def send_document_register(self):
        if self._send_json({
            'DocElectronicos': [
                self._get_doc(),
            ],
        }, self.company_id.ei_service_document_register):
            self.action_invoice_open()

    def _send_json(self, body, api):
        # TODO checks
        conn = http.client.HTTPSConnection(self.company_id.ei_url_api)
        body['CodigoCliente'] = self.company_id.ei_id_user
        headers = {
            'Content-Type': 'application/json',
            'Usuario': self.company_id.ei_user,
            'UsuarioClave': self.company_id.ei_password,
            'CodigoCliente': self.company_id.ei_id_user,
        }
        _logger.info('Sending JSON %s', body)
        try:
            conn.request("POST", api, json.dumps(body), headers)
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
                self.ei_state = 'to_query'
                self.ei_message = _('Document received, waiting for query.')
            return self.ei_response_code == '1'

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
        conn.request('POST', self.company_id.ei_service_document_query, '', headers)
        response = json.loads(conn.getresponse().read().decode('utf-8'))
        self.ei_response_code = response['CodigoRespuesta']
        self.ei_message = response['Mensaje']
        self.ei_date = response['Fecha']
        if self.ei_response_code == '1':
            try:
                _logger.info('Response {}'.format(response['Id']))
                self.ei_status_code = response['CodigoEstado']
                if self.ei_status_code == '4':
                    self.ei_state = 'queried'
                    self.electronic_invoice_pdf = 'http://factura.apifecr.com#{}.pdf'.format(self.key)
                self.ei_status_desc = response['DescripcionEstado']
                self.ei_message_response = response['MensajeRespuesta']
                self.electronic_invoice_xml_signed = response['XMLFirmado']
                self.electronic_invoice_xml = response['XMLRespuesta']
            except KeyError:
                raise ValidationError(_('No answer from the API.'))
        return response

    def _get_invoice_from_xml(self):
        if not self.xml_supplier_approval:
            raise ValidationError(_('No XML loaded'))

        xml_decoded = b64decode(self.xml_supplier_approval)

        try:
            invoice = etree.fromstring(xml_decoded)
        except Exception as e:
            _logger.error('XML can not be parsed.  Exception %s' % e)
            raise ValidationError(_('XML can not be parsed'))
        else:
            # _logger.info('Loading XML: %s ' % etree.tostring(invoice, pretty_print=True, encoding='UTF-8', xml_declaration=True))

            for elem in invoice.getiterator():
                elem.tag = etree.QName(elem).localname
            return invoice

    def load_xml_data(self):
        invoice = self._get_invoice_from_xml()

        self.key = get(invoice, 'Clave')
        self.activity_id = self.env['res.company.activity'].search([('code', '=', get(invoice, 'CodigoActividad'))])
        emission_date = get(invoice, 'FechaEmision')
        date_formats = [
            '%Y-%m-%dT%H:%M:%S-06:00',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
        ]
        for date_format in date_formats:
            try:
                date_time_obj = datetime.strptime(emission_date, date_format)
                break
            except ValueError:
                continue
        else:
            raise ValueError(_('No valid date format for {}').format(emission_date))
        local = pytz.timezone(self.env.user.tz or pytz.utc.zone)
        self.emission_date = date_time_obj - local.utcoffset(fields.Datetime.now())
        self.date_invoice = self.emission_date.date()
        if get(invoice, 'Receptor/Identificacion/Numero') != self.company_id.vat:
            raise ValidationError(_('Receptor VAT is not the same as in the company.'))
        partner_vat = get(invoice, 'Emisor/Identificacion/Numero')
        partner_id = self.env['res.partner'].search([
            ('vat', '=', partner_vat),
            ('supplier', '=', True),
            '|',
            ('company_id', '=', self.company_id.id),
            ('company_id', '=', False),
        ], limit=1)
        if not partner_id:
            raise ValidationError(_('The partner with VAT {} does not exists').format(partner_vat))
        self.partner_id = partner_id
        # TODO self._get_lines_from_invoice(invoice)

    def _get_lines_from_invoice(self, invoice):
        self.invoice_line_ids.unlink()
        for line in invoice.xpath('DetalleServicio/LineaDetalle'):
            line_id = self.env['account.invoice.line'].create({
                'account_id': self.env['account.account'].search([('code', '=', '0-511301')]).id,  # TODO
                'product_id': 1,  # TODO
                'name': get(line, 'Detalle'),
                'price_unit': get(line, 'PrecioUnitario'),
                'quantity': get(line, 'Cantidad'),
            })
            for tax in line.xpath('Impuesto'):
                line_id.invoice_line_tax_ids |= self.env['account.tax'].search([('code', '=', get(tax, 'Codigo'))], limit=1)
            discount = line.xpath('Descuento/MontoDescuento')
            discount = discount and float(discount[0].text)
            if discount:
                line_id.discount = (discount / (line_id.price_unit * line_id.quantity)) * 100
            self.invoice_line_ids |= line_id
        self._compute_amount()

    def send_message_register(self):
        self._send_json({
            'DocMensajeReceptor': {
                'TipoDocumento': self.doc_type,
                'SecuenciaControlada': 1,
                # 'NumeroConsecutivoReceptor': '',
                # 'SecienciaDocumento': 0,
                'Sucursal': self.company_id.ei_sucursal,
                'Terminal': self.company_id.ei_terminal,
                'Clave': self.key,
                'NumeroCedulaEmisor': self.partner_id.vat,
                'TipoCedulaEmisor': self.partner_id.identification_type,
                'FechaEmisionDoc': datetime.strftime(fields.Datetime.context_timestamp(self, self.emission_date), '%Y-%m-%dT%H:%M:%S'),
                # 'Mensaje': 1,
                # 'DetalleMensaje': '',
                'MontoTotalImpuesto': self.amount_tax,
                'CodigoActividad': self.activity_id.code,
                'CondicionImpuesto': '01',  # zxc
                'MontoTotalImpuestoAcreditar': 0,  # zxc
                'MontoTotalDeGastoAplicable': 0,  # zxc
                'TotalFactura': self.amount_total,
                'NumeroCedulaReceptor': self.company_id.vat,
            }
        }, self.company_id.ei_service_message_register)
