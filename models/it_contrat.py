# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ItContrat(models.Model):
    _name = 'it.contrat'
    _description = 'Contrat fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_fin asc'

    name = fields.Char(string='Référence contrat', required=True, tracking=True)
    type_contrat = fields.Selection([
        ('maintenance', 'Maintenance'),
        ('licence',     'Licence logicielle'),
        ('support',     'Support technique'),
        ('autre',       'Autre'),
    ], string='Type', required=True, default='maintenance', tracking=True)
    fournisseur_id = fields.Many2one('res.partner', string='Fournisseur', required=True, tracking=True)
    date_debut = fields.Date(string='Date début', required=True, tracking=True)
    date_fin = fields.Date(string="Date d'expiration", required=True, tracking=True)
    montant = fields.Float(string='Montant (FCFA)', tracking=True)
    jours_restants = fields.Integer(string='Jours restants', compute='_compute_jours', store=True)
    est_expire = fields.Boolean(string='Expiré', compute='_compute_jours', store=True)
    expire_bientot = fields.Boolean(string='Expire bientôt (60j)', compute='_compute_jours', store=True)
    equipement_ids = fields.Many2many('it.equipement', 'it_contrat_equipement_rel', 'contrat_id', 'equipement_id', string='Équipements couverts')
    nb_equipements = fields.Integer(string='Nb équipements', compute='_compute_nb_equipements')
    etat = fields.Selection([
        ('actif',     'Actif'),
        ('expire',    'Expiré'),
        ('resilie',   'Résilié'),
        ('renouvele', 'Renouvelé'),
    ], string='État', default='actif', required=True, tracking=True)
    notes = fields.Text(string='Notes')

    @api.depends('date_fin')
    def _compute_jours(self):
        today = fields.Date.today()
        for rec in self:
            if rec.date_fin:
                delta = (rec.date_fin - today).days
                rec.jours_restants = delta
                rec.est_expire = delta < 0
                rec.expire_bientot = 0 <= delta <= 60
            else:
                rec.jours_restants = 0
                rec.est_expire = False
                rec.expire_bientot = False

    @api.depends('equipement_ids')
    def _compute_nb_equipements(self):
        for rec in self:
            rec.nb_equipements = len(rec.equipement_ids)
