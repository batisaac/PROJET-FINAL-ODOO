# -*- coding: utf-8 -*-
import base64
import csv
import io
from odoo import models, fields, api
from odoo.exceptions import UserError


class WizardImportCsv(models.TransientModel):
    _name = 'wizard.import.csv'
    _description = "Assistant d'import CSV d'équipements"

    fichier_csv = fields.Binary(string='Fichier CSV', required=True)
    nom_fichier = fields.Char(string='Nom du fichier')
    nb_crees = fields.Integer(string='Créés', readonly=True)
    nb_ignores = fields.Integer(string='Ignorés (doublons)', readonly=True)
    nb_erreurs = fields.Integer(string='Erreurs', readonly=True)
    rapport = fields.Text(string='Détail du rapport', readonly=True)
    import_effectue = fields.Boolean(default=False)

    def action_importer(self):
        self.ensure_one()
        if not self.fichier_csv:
            raise UserError("Veuillez sélectionner un fichier CSV.")

        raw = base64.b64decode(self.fichier_csv)
        try:
            contenu = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            contenu = raw.decode('latin-1')
        reader = csv.DictReader(io.StringIO(contenu, newline=''), delimiter=',')

        nb_crees = 0
        nb_ignores = 0
        nb_erreurs = 0
        lignes_rapport = []

        colonnes_requises = {'nom', 'numero_serie', 'categorie', 'marque', 'modele'}

        for i, row in enumerate(reader, start=2):
            manquantes = colonnes_requises - set(row.keys())
            if manquantes:
                raise UserError(
                    f"Colonnes manquantes dans le CSV : {', '.join(manquantes)}\n"
                    f"Colonnes attendues : nom, numero_serie, categorie, marque, modele"
                )

            nom = row.get('nom', '').strip()
            numero_serie = row.get('numero_serie', '').strip()

            if not nom or not numero_serie:
                nb_erreurs += 1
                lignes_rapport.append(f"Ligne {i} : nom ou numéro de série manquant — ignorée.")
                continue

            existant = self.env['it.equipement'].search(
                [('numero_serie', '=', numero_serie)], limit=1
            )
            if existant:
                nb_ignores += 1
                lignes_rapport.append(
                    f"Ligne {i} : [{numero_serie}] déjà existant ({existant.nom}) — ignoré."
                )
                continue

            categorie_nom = row.get('categorie', '').strip()
            categorie = self.env['product.category'].search(
                [('name', '=', categorie_nom)], limit=1
            )
            if not categorie:
                categorie = self.env['product.category'].create({'name': categorie_nom})

            try:
                self.env['it.equipement'].create({
                    'nom': nom,
                    'numero_serie': numero_serie,
                    'categorie_id': categorie.id,
                    'marque': row.get('marque', '').strip(),
                    'modele': row.get('modele', '').strip(),
                    'localisation': row.get('localisation', '').strip(),
                    'valeur_achat': float(row.get('valeur_achat', 0) or 0),
                })
                nb_crees += 1
                lignes_rapport.append(f"Ligne {i} : [{numero_serie}] {nom} — créé ✓")
            except Exception as e:
                nb_erreurs += 1
                lignes_rapport.append(f"Ligne {i} : erreur — {str(e)}")

        self.write({
            'nb_crees': nb_crees,
            'nb_ignores': nb_ignores,
            'nb_erreurs': nb_erreurs,
            'rapport': '\n'.join(lignes_rapport),
            'import_effectue': True,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.import.csv',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }