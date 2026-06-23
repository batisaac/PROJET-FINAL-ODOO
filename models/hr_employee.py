# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    affectation_ids = fields.One2many(
        'it.affectation',
        'employe_id',
        string='Équipements affectés'
    )