/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, useRef, onMounted, onPatched } from "@odoo/owl";

class ItDashboard extends Component {
    static template = "it_parc.ItDashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            totalActifs: 0,
            tauxDisponibilite: 0,
            alertesActives: 0,
            coutAnnee: 0,
            repartitionCategories: [],
            loading: true,
        });
        this.canvasRef = useRef("chartCanvas");

        onWillStart(async () => {
            await this.loadData();
        });

        onMounted(() => {
            this.renderChart();
        });

        onPatched(() => {
            if (!this.state.loading) {
                this.renderChart();
            }
        });
    }

    async loadData() {
        const annee = new Date().getFullYear();
        const debutAnnee = `${annee}-01-01`;
        const finAnnee = `${annee}-12-31`;

        // KPI 1 : Total équipements actifs (hors retirés)
        const totalActifs = await this.orm.searchCount("it.equipement", [
            ["etat", "!=", "retire"]
        ]);
        this.state.totalActifs = totalActifs;

        // KPI 2 : Taux de disponibilité
        const totalAffectes = await this.orm.searchCount("it.equipement", [
            ["etat", "=", "affecte"]
        ]);
        this.state.tauxDisponibilite = totalActifs > 0
            ? Math.round((totalAffectes / totalActifs) * 100)
            : 0;

        // KPI 3 : Alertes actives
        const alertesActives = await this.orm.searchCount("it.alerte", [
            ["etat", "=", "active"]
        ]);
        this.state.alertesActives = alertesActives;

        // KPI 4 : Coût total maintenance année en cours
        const interventions = await this.orm.searchRead(
            "it.intervention",
            [
                ["schedule_date", ">=", debutAnnee],
                ["schedule_date", "<=", finAnnee],
            ],
            ["cout"]
        );
        this.state.coutAnnee = interventions.reduce(
            (sum, i) => sum + (i.cout || 0), 0
        );

        // Graphique : répartition par catégorie
        const equipements = await this.orm.searchRead(
            "it.equipement",
            [["etat", "!=", "retire"]],
            ["categorie_id"]
        );

        const parCategorie = {};
        for (const eq of equipements) {
            const nom = eq.categorie_id ? eq.categorie_id[1] : "Non classé";
            parCategorie[nom] = (parCategorie[nom] || 0) + 1;
        }

        this.state.repartitionCategories = Object.entries(parCategorie)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 6);

        this.state.loading = false;
    }

    renderChart() {
        const canvas = this.canvasRef.el;
        if (!canvas || !this.state.repartitionCategories.length) return;

        const ctx = canvas.getContext("2d");
        const data = this.state.repartitionCategories;
        const maxVal = Math.max(...data.map(d => d[1])) || 1;

        const barHeight = 36;
        const gap = 12;
        const paddingLeft = 160;
        const paddingTop = 20;
        const chartWidth = 400;

        canvas.width = paddingLeft + chartWidth + 60;
        canvas.height = paddingTop + data.length * (barHeight + gap) + 20;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const couleurs = [
            "#2d2d6b", "#4a90d9", "#28a745", "#ffc107",
            "#dc3545", "#6f42c1"
        ];

        data.forEach(([label, count], i) => {
            const y = paddingTop + i * (barHeight + gap);
            const barW = (count / maxVal) * chartWidth;

            // Label à gauche
            ctx.fillStyle = "#495057";
            ctx.font = "13px Arial";
            ctx.textAlign = "right";
            const shortLabel = label.length > 20 ? label.slice(0, 20) + "…" : label;
            ctx.fillText(shortLabel, paddingLeft - 10, y + barHeight / 2 + 4);

            // Barre
            ctx.fillStyle = couleurs[i % couleurs.length];
            ctx.beginPath();
            ctx.roundRect
                ? ctx.roundRect(paddingLeft, y, barW, barHeight, 4)
                : ctx.rect(paddingLeft, y, barW, barHeight);
            ctx.fill();

            // Valeur à droite
            ctx.fillStyle = "#212529";
            ctx.font = "bold 13px Arial";
            ctx.textAlign = "left";
            ctx.fillText(count, paddingLeft + barW + 8, y + barHeight / 2 + 4);
        });
    }

    formatMontant(val) {
        return new Intl.NumberFormat("fr-FR").format(Math.round(val)) + " FCFA";
    }

    async refresh() {
        this.state.loading = true;
        await this.loadData();
        // Attendre que le DOM soit mis à jour avant de dessiner
        await new Promise(resolve => setTimeout(resolve, 50));
        this.renderChart();
    }
}

registry.category("actions").add("it_parc.dashboard", ItDashboard);