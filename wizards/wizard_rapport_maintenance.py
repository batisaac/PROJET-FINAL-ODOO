# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class WizardRapportMaintenance(models.TransientModel):
    _name = 'wizard.rapport.maintenance'
    _description = 'Assistant rapport de maintenance par période'

    date_debut = fields.Date(string='Date début', required=True)
    date_fin = fields.Date(string='Date fin', required=True)

    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        for rec in self:
            if rec.date_debut > rec.date_fin:
                raise UserError("La date de début doit être antérieure à la date de fin.")

    def action_imprimer(self):
        self.ensure_one()
        interventions = self.env['it.intervention'].search([
            ('schedule_date', '>=', self.date_debut),
            ('schedule_date', '<=', self.date_fin),
        ])
        if not interventions:
            raise UserError("Aucune intervention trouvée pour cette période.")
        return self.env.ref('it_parc.action_report_maintenance').report_action(interventions)