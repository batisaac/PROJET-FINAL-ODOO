# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class WizardReaffectation(models.TransientModel):
    _name = 'wizard.reaffectation'
    _description = "Assistant de réaffectation d'équipement"

    equipement_id = fields.Many2one(
        'it.equipement',
        string='Équipement',
        required=True,
        readonly=True,
    )
    ancien_employe_id = fields.Many2one(
        'hr.employee',
        string='Employé actuel',
        readonly=True,
    )
    nouvel_employe_id = fields.Many2one(
        'hr.employee',
        string='Nouvel employé',
        required=True,
    )
    motif = fields.Text(string='Motif de réaffectation', required=True)
    date_reaffectation = fields.Date(
        string='Date de réaffectation',
        required=True,
        default=fields.Date.today,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Pré-remplir depuis l'équipement actif
        equipement_id = self.env.context.get('active_id')
        if equipement_id:
            eq = self.env['it.equipement'].browse(equipement_id)
            res['equipement_id'] = eq.id
            res['ancien_employe_id'] = eq.employe_id.id
        return res

    def action_confirmer(self):
        self.ensure_one()
        eq = self.equipement_id

        if self.nouvel_employe_id == eq.employe_id:
            raise UserError("Le nouvel employé est identique à l'employé actuel.")

        # Clôturer l'affectation courante
        affectation_courante = self.env['it.affectation'].search([
            ('equipement_id', '=', eq.id),
            ('est_actuelle', '=', True),
        ], limit=1)
        if affectation_courante:
            affectation_courante.date_retour = self.date_reaffectation

        # Créer la nouvelle affectation
        self.env['it.affectation'].create({
            'equipement_id': eq.id,
            'employe_id': self.nouvel_employe_id.id,
            'date_affectation': self.date_reaffectation,
            'motif': self.motif,
        })

        # Mettre à jour l'équipement
        eq.employe_id = self.nouvel_employe_id
        eq.etat = 'affecte'

        # Message dans le chatter
        eq.message_post(
            body=f"Réaffectation : {self.ancien_employe_id.name or 'Non affecté'} "
                 f"→ {self.nouvel_employe_id.name}. Motif : {self.motif}",
            message_type='notification',
        )

        return {'type': 'ir.actions.act_window_close'}