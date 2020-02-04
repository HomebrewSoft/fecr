# coding: utf-8
{
    'name': 'Costa Rica Electronic Invoice',
    'version': '1.5.0',
    'author': 'Navarro Moisés',
    'website': 'https://github.com/lfelipecr/xalachi-fecr',
    'category': 'Localization',
    'depends': [
        'l10n_cr',
        'uom',
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        'data/account_tax.xml',
        'data/ir_cron.xml',
        'data/res_company_activity.xml',
        'data/res.country.state.csv',
        'data/res.country.county.csv',
        'data/res.country.district.csv',
        'data/res.country.neighborhood.csv',
        'data/uom_uom.xml',
        # views
        'views/account_invoice.xml',
        'views/account_tax.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/uom_uom.xml',
    ],
    'external_dependencies': {
        'python': [
        ]
    }
}
