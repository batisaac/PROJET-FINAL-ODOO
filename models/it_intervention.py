# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ItIntervention(models.Model):
    _name = 'it.intervention'
    _inherit = 'maintenance.request'
    _description = 'Intervention de maintenance IT'

    type_intervention = fields.Selection([
        ('corrective', 'Corrective'),
        ('preventive', 'Préventive'),
    ], string='Type', required=True, default='corrective', tracking=True)

    cout = fields.Float(string='Coût (FCFA)', tracking=True)

    rapport_intervention = fields.Text(string="Rapport d'intervention")

    duree_heures = fields.Float(
        string='Durée (h)',
        compute='_compute_duree',
        store=True
    )

    equipement_id = fields.Many2one('it.equipement', string='Équipement IT', tracking=True)

    @api.depends('schedule_date', 'close_date')
    def _compute_duree(self):
        for rec in self:
            if rec.schedule_date and rec.close_date:
                rec.duree_heures = (rec.close_date - rec.schedule_date).total_seconds() / 3600
            else:
                rec.duree_heures = 0.0