# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ItAffectation(models.Model):
    _name = 'it.affectation'
    _description = "Historique des affectations d'équipement"
    _inherit = ['mail.thread']
    _order = 'date_affectation desc'

    equipement_id = fields.Many2one('it.equipement', string='Équipement', required=True, ondelete='cascade')
    employe_id = fields.Many2one('hr.employee', string='Employé', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Département', related='employe_id.department_id', store=True)
    date_affectation = fields.Date(string="Date d'affectation", required=True, default=fields.Date.today, tracking=True)
    date_retour = fields.Date(string='Date de retour', tracking=True)
    motif = fields.Text(string='Motif', tracking=True)
    est_actuelle = fields.Boolean(string='En cours', compute='_compute_est_actuelle', store=True)
    duree_jours = fields.Integer(string='Durée (jours)', compute='_compute_duree', store=True)

    @api.depends('date_retour')
    def _compute_est_actuelle(self):
        for rec in self:
            rec.est_actuelle = not rec.date_retour

    @api.depends('date_affectation', 'date_retour')
    def _compute_duree(self):
        today = fields.Date.today()
        for rec in self:
            if rec.date_affectation:
                fin = rec.date_retour or today
                rec.duree_jours = (fin - rec.date_affectation).days
            else:
                rec.duree_jours = 0
