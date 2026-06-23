# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contrat_ids = fields.One2many(
        'it.contrat',
        'fournisseur_id',
        string='Contrats IT'
    )