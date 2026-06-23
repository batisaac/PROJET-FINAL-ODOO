# -*- coding: utf-8 -*-
import io
import base64
import xlsxwriter
from odoo import models, fields, api


class ItEquipementExport(models.Model):
    _inherit = 'it.equipement'

    def action_export_inventaire(self):
        """Export Excel : inventaire complet de tous les équipements."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Inventaire')

        # Styles
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#2d2d6b', 'font_color': 'white',
            'border': 1, 'align': 'center'
        })
        row_fmt = workbook.add_format({'border': 1})
        row_alt = workbook.add_format({'border': 1, 'bg_color': '#f2f2f2'})
        warning_fmt = workbook.add_format({
            'border': 1, 'bg_color': '#fff3cd'
        })
        danger_fmt = workbook.add_format({
            'border': 1, 'bg_color': '#f8d7da'
        })

        # En-têtes
        headers = [
            'Référence', 'Nom', 'Catégorie', 'Marque', 'Modèle',
            'N° Série', 'Employé', 'Département', 'Localisation',
            'Valeur achat (FCFA)', 'Date achat', 'Fin garantie',
            'Jours garantie', 'État', 'Coût maintenance (FCFA)'
        ]
        for col, h in enumerate(headers):
            sheet.write(0, col, h, header_fmt)
            sheet.set_column(col, col, 18)

        # Données
        equipements = self.search([])
        for row, eq in enumerate(equipements, start=1):
            fmt = row_fmt if row % 2 == 0 else row_alt
            if eq.garantie_expiree:
                fmt = danger_fmt
            elif eq.jours_garantie_restants <= 30 and eq.jours_garantie_restants >= 0:
                fmt = warning_fmt

            sheet.write(row, 0, eq.reference or '', fmt)
            sheet.write(row, 1, eq.nom or '', fmt)
            sheet.write(row, 2, eq.categorie_id.name or '', fmt)
            sheet.write(row, 3, eq.marque or '', fmt)
            sheet.write(row, 4, eq.modele or '', fmt)
            sheet.write(row, 5, eq.numero_serie or '', fmt)
            sheet.write(row, 6, eq.employe_id.name or '', fmt)
            sheet.write(row, 7, eq.department_id.name or '', fmt)
            sheet.write(row, 8, eq.localisation or '', fmt)
            sheet.write(row, 9, eq.valeur_achat or 0, fmt)
            sheet.write(row, 10, str(eq.date_achat) if eq.date_achat else '', fmt)
            sheet.write(row, 11, str(eq.date_fin_garantie) if eq.date_fin_garantie else '', fmt)
            sheet.write(row, 12, eq.jours_garantie_restants or 0, fmt)
            sheet.write(row, 13, dict(eq._fields['etat'].selection).get(eq.etat, ''), fmt)
            sheet.write(row, 14, eq.cout_total_maintenance or 0, fmt)

        workbook.close()
        output.seek(0)

        # Retourner comme pièce jointe téléchargeable
        attachment = self.env['ir.attachment'].create({
            'name': 'inventaire_parc_informatique.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class ItInterventionExport(models.Model):
    _inherit = 'it.intervention'

    def action_export_couts_maintenance(self):
        """Export Excel : synthèse des coûts de maintenance par asset et par mois."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Coûts maintenance')

        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#2d2d6b', 'font_color': 'white',
            'border': 1, 'align': 'center'
        })
        row_fmt = workbook.add_format({'border': 1})
        row_alt = workbook.add_format({'border': 1, 'bg_color': '#f2f2f2'})
        total_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': '#d4edda'
        })

        headers = [
            'Équipement', 'Référence', 'Mois', 'Année',
            'Nb interventions', 'Durée totale (h)', 'Coût total (FCFA)'
        ]
        for col, h in enumerate(headers):
            sheet.write(0, col, h, header_fmt)
            sheet.set_column(col, col, 20)

        # Regrouper par équipement et par mois
        interventions = self.search([('schedule_date', '!=', False)])
        data = {}
        for inter in interventions:
            eq = inter.equipement_id
            eq_name = eq.nom if eq else (inter.equipment_id.name if inter.equipment_id else 'N/A')
            eq_ref = eq.reference if eq else ''
            mois = inter.schedule_date.month if inter.schedule_date else 0
            annee = inter.schedule_date.year if inter.schedule_date else 0
            key = (eq_name, eq_ref, mois, annee)
            if key not in data:
                data[key] = {'nb': 0, 'duree': 0, 'cout': 0}
            data[key]['nb'] += 1
            data[key]['duree'] += inter.duree_heures or 0
            data[key]['cout'] += inter.cout or 0

        mois_noms = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }

        total_cout = 0
        for row, ((eq_name, eq_ref, mois, annee), vals) in enumerate(
            sorted(data.items(), key=lambda x: (x[0][0], x[0][3], x[0][2])), start=1
        ):
            fmt = row_fmt if row % 2 == 0 else row_alt
            sheet.write(row, 0, eq_name, fmt)
            sheet.write(row, 1, eq_ref, fmt)
            sheet.write(row, 2, mois_noms.get(mois, ''), fmt)
            sheet.write(row, 3, annee, fmt)
            sheet.write(row, 4, vals['nb'], fmt)
            sheet.write(row, 5, round(vals['duree'], 1), fmt)
            sheet.write(row, 6, vals['cout'], fmt)
            total_cout += vals['cout']

        # Ligne total
        last_row = len(data) + 1
        sheet.write(last_row, 0, 'TOTAL', total_fmt)
        sheet.write(last_row, 5, '', total_fmt)
        sheet.write(last_row, 6, total_cout, total_fmt)

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'couts_maintenance.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class ItContratExport(models.Model):
    _inherit = 'it.contrat'

    def action_export_contrats_expirants(self):
        """Export Excel : contrats expirant dans les 60 prochains jours."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Contrats expirants')

        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#2d2d6b', 'font_color': 'white',
            'border': 1, 'align': 'center'
        })
        normal_fmt = workbook.add_format({'border': 1})
        warning_fmt = workbook.add_format({
            'border': 1, 'bg_color': '#fff3cd'  # orange clair : expire entre 31 et 60j
        })
        danger_fmt = workbook.add_format({
            'border': 1, 'bg_color': '#f8d7da'  # rouge clair : expire dans 30j ou moins
        })
        expire_fmt = workbook.add_format({
            'border': 1, 'bg_color': '#d6d6d6'  # gris : déjà expiré
        })

        headers = [
            'Référence', 'Type', 'Fournisseur', 'Date début',
            'Date expiration', 'Jours restants', 'Montant (FCFA)',
            'Nb équipements', 'État', 'Statut alerte'
        ]
        for col, h in enumerate(headers):
            sheet.write(0, col, h, header_fmt)
            sheet.set_column(col, col, 20)

        contrats = self.search([
            ('etat', '=', 'actif'),
            ('jours_restants', '<=', 60),
        ], order='jours_restants asc')

        for row, c in enumerate(contrats, start=1):
            # Couleur conditionnelle selon urgence
            if c.est_expire:
                fmt = expire_fmt
                statut = '❌ Expiré'
            elif c.jours_restants <= 30:
                fmt = danger_fmt
                statut = '🔴 Urgent (≤ 30j)'
            else:
                fmt = warning_fmt
                statut = '🟡 Attention (31-60j)'

            sheet.write(row, 0, c.name or '', fmt)
            sheet.write(row, 1, dict(c._fields['type_contrat'].selection).get(c.type_contrat, ''), fmt)
            sheet.write(row, 2, c.fournisseur_id.name or '', fmt)
            sheet.write(row, 3, str(c.date_debut) if c.date_debut else '', fmt)
            sheet.write(row, 4, str(c.date_fin) if c.date_fin else '', fmt)
            sheet.write(row, 5, c.jours_restants, fmt)
            sheet.write(row, 6, c.montant or 0, fmt)
            sheet.write(row, 7, c.nb_equipements, fmt)
            sheet.write(row, 8, dict(c._fields['etat'].selection).get(c.etat, ''), fmt)
            sheet.write(row, 9, statut, fmt)

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'contrats_expirants_60j.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }