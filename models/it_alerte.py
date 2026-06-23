# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ItAlerte(models.Model):
    _name = 'it.alerte'
    _description = "Alerte de garantie ou d'expiration de contrat"
    _inherit = ['mail.thread']
    _order = 'date_echeance asc'

    name = fields.Char(string="Titre de l'alerte", required=True, tracking=True)
    type_alerte = fields.Selection([
        ('garantie', 'Fin de garantie'),
        ('contrat',  'Expiration de contrat'),
    ], string='Type', required=True, tracking=True)
    equipement_id = fields.Many2one('it.equipement', string='Équipement', ondelete='cascade')
    contrat_id = fields.Many2one('it.contrat', string='Contrat', ondelete='cascade')
    date_echeance = fields.Date(string="Date d'échéance", required=True, tracking=True)
    jours_restants = fields.Integer(string='Jours restants', compute='_compute_jours', store=True)
    etat = fields.Selection([
        ('active',  'Active'),
        ('traitee', 'Traitée'),
        ('ignoree', 'Ignorée'),
    ], string='État', default='active', required=True, tracking=True)
    message = fields.Text(string='Détails')

    @api.depends('date_echeance')
    def _compute_jours(self):
        today = fields.Date.today()
        for rec in self:
            rec.jours_restants = (rec.date_echeance - today).days if rec.date_echeance else 0

    def action_traiter(self):
        for rec in self:
            rec.etat = 'traitee'

    def action_ignorer(self):
        for rec in self:
            rec.etat = 'ignoree'

    @api.model
    def generer_alertes(self, delai_jours=30):
        today = fields.Date.today()
        for eq in self.env['it.equipement'].search([('date_fin_garantie', '!=', False), ('etat', '!=', 'retire')]):
            delta = (eq.date_fin_garantie - today).days
            if 0 <= delta <= delai_jours:
                if not self.search([('equipement_id', '=', eq.id), ('type_alerte', '=', 'garantie'), ('etat', '=', 'active')]):
                    self.create({'name': f"Garantie expirant : {eq.nom}", 'type_alerte': 'garantie', 'equipement_id': eq.id, 'date_echeance': eq.date_fin_garantie, 'message': f"Expire dans {delta} jour(s)."})
        for contrat in self.env['it.contrat'].search([('etat', '=', 'actif'), ('date_fin', '!=', False)]):
            delta = (contrat.date_fin - today).days
            if 0 <= delta <= delai_jours:
                if not self.search([('contrat_id', '=', contrat.id), ('type_alerte', '=', 'contrat'), ('etat', '=', 'active')]):
                    self.create({'name': f"Contrat expirant : {contrat.name}", 'type_alerte': 'contrat', 'contrat_id': contrat.id, 'date_echeance': contrat.date_fin, 'message': f"Expire dans {delta} jour(s)."})

    def action_generer_maintenant(self):
        self.generer_alertes(delai_jours=30)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Scan terminé',
                'message': 'Les alertes ont été générées avec succès.',
                'type': 'success',
                'sticky': False,
            },
        }