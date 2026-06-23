# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class ItEquipement(models.Model):
    _name = 'it.equipement'
    _description = 'Équipement informatique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'nom asc'
    _rec_name = 'nom'

    nom = fields.Char(string='Nom', required=True, tracking=True)
    reference = fields.Char(string='Référence', copy=False, readonly=True, default='/')
    numero_serie = fields.Char(string='Numéro de série', required=True, copy=False, tracking=True)
    categorie_id = fields.Many2one('product.category', string='Catégorie', required=True, tracking=True)
    marque = fields.Char(string='Marque', tracking=True)
    modele = fields.Char(string='Modèle', tracking=True)
    description = fields.Text(string='Caractéristiques techniques')

    valeur_achat = fields.Float(string='Valeur achat (FCFA)', tracking=True)
    date_achat = fields.Date(string='Date achat', tracking=True)
    date_fin_garantie = fields.Date(string='Fin de garantie', tracking=True)
    garantie_expiree = fields.Boolean(string='Garantie expirée', compute='_compute_garantie', store=True)
    jours_garantie_restants = fields.Integer(string='Jours garantie restants', compute='_compute_garantie', store=True)

    employe_id = fields.Many2one('hr.employee', string='Employé affecté', tracking=True)
    department_id = fields.Many2one('hr.department', string='Département', related='employe_id.department_id', store=True, readonly=False, tracking=True)
    localisation = fields.Char(string='Localisation / Site', tracking=True)

    etat = fields.Selection([
        ('brouillon',   'Brouillon'),
        ('affecte',     'Affecté'),
        ('maintenance', 'En maintenance'),
        ('retire',      'Retiré'),
    ], string='État', default='brouillon', required=True, tracking=True)

    affectation_ids = fields.One2many('it.affectation', 'equipement_id', string='Historique affectations')
    intervention_ids = fields.One2many('it.intervention', 'equipement_id', string='Interventions')
    contrat_ids = fields.Many2many('it.contrat', 'it_contrat_equipement_rel', 'equipement_id', 'contrat_id', string='Contrats')
    alerte_ids = fields.One2many('it.alerte', 'equipement_id', string='Alertes')

    nb_interventions = fields.Integer(string='Nb interventions', compute='_compute_stats')
    nb_alertes = fields.Integer(string='Alertes actives', compute='_compute_stats')
    cout_total_maintenance = fields.Float(string='Coût total maintenance (FCFA)', compute='_compute_cout', store=True)

    @api.depends('date_fin_garantie')
    def _compute_garantie(self):
        today = fields.Date.today()
        for rec in self:
            if rec.date_fin_garantie:
                delta = (rec.date_fin_garantie - today).days
                rec.jours_garantie_restants = delta
                rec.garantie_expiree = delta < 0
            else:
                rec.jours_garantie_restants = 0
                rec.garantie_expiree = False

    @api.depends('intervention_ids', 'alerte_ids', 'alerte_ids.etat')
    def _compute_stats(self):
        for rec in self:
            rec.nb_interventions = len(rec.intervention_ids)
            rec.nb_alertes = len(rec.alerte_ids.filtered(lambda a: a.etat == 'active'))

    @api.depends('intervention_ids', 'intervention_ids.cout')
    def _compute_cout(self):
        for rec in self:
            rec.cout_total_maintenance = sum(rec.intervention_ids.mapped('cout'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', '/') == '/':
                vals['reference'] = self.env['ir.sequence'].next_by_code('it.equipement') or '/'
        return super().create(vals_list)

    def action_affecter(self):
        for rec in self:
            if not rec.employe_id:
                raise UserError("Veuillez affecter un employé avant de valider.")
            rec.etat = 'affecte'

    def action_mettre_en_maintenance(self):
        for rec in self:
            rec.etat = 'maintenance'

    def action_retirer(self):
        for rec in self:
            rec.etat = 'retire'

    def action_remettre_brouillon(self):
        for rec in self:
            rec.etat = 'brouillon'
    
    def action_open_reaffectation(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Réaffecter',
            'res_model': 'wizard.reaffectation',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }
    
    _sql_constraints = [
    ('numero_serie_unique', 'UNIQUE(numero_serie)', 'Un équipement avec ce numéro de série existe déjà.'),
]