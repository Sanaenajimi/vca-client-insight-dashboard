# Client Insight & Data — Portfolio Data Analyst

Projet portfolio construit pour une candidature au poste de **Data Analyst**,
département **Client Insight & Data**, d'une maison de joaillerie de luxe.

**Dashboard en ligne :** _(à publier via GitHub Pages — voir section Déploiement)_

> **Toutes les données de ce projet sont 100% simulées.** Aucune donnée
> réelle, logo, photo ou visuel d'une maison de joaillerie existante n'est
> utilisé. Ce projet est un exercice pédagogique de portfolio technique.

---

## Pourquoi ce projet

L'offre de poste couvre deux volets qui se répondent : une expertise **valeur
et fidélisation client** (CLV, rétention, panier moyen, RFM) et une expertise
**parcours client omnicanal** (boutique / digital / événementiel), le tout au
service d'une mission transverse d'**harmonisation des indicateurs entre le
siège et les marchés**. Ce projet reproduit cette chaîne complète, de la
donnée brute au dashboard de restitution, pour démontrer une approche
concrète plutôt que déclarative de ces sujets.

## Ce que couvre le projet

| Thématique | Où | Détail |
|---|---|---|
| Génération de données | `data/` | Base clients / transactions / points de contact CRM multi-marchés, 24 mois, avec dynamique comportementale réaliste |
| Requêtes SQL | `sql/` | 6 requêtes BigQuery : CLV, rétention/cohortes, panier moyen, mix omnicanal, harmonisation marchés, segmentation RFM |
| Analyse Python | `analysis/` | Script pandas qui recalcule les mêmes indicateurs et exporte le JSON consommé par le dashboard |
| Documentation KPI | `kpi-documentation/` | Définition, formule, usage métier et limites de chaque indicateur |
| Dashboard | `dashboard/` | Restitution en une page HTML autonome, esthétique "maison de luxe" (ivoire / noir / or), thème clair/sombre |

## Structure du repo

```
vca-client-insight-portfolio/
├── data/
│   ├── generate_synthetic_data.py      # génération des 3 tables sources
│   ├── customers.csv
│   ├── transactions.csv
│   └── touchpoints.csv
├── sql/
│   ├── 01_clv_par_marche_tier.sql
│   ├── 02_retention_cohortes.sql
│   ├── 03_panier_moyen_frequence.sql
│   ├── 04_mix_omnicanal.sql
│   ├── 05_harmonisation_marches.sql
│   └── 06_segmentation_rfm.sql
├── analysis/
│   └── build_dashboard_data.py         # pandas -> dashboard/vca_dashboard_data.json
├── kpi-documentation/
│   └── documentation_kpis.md
├── dashboard/
│   ├── vca_client_insight_dashboard.html   # dashboard autonome (1 fichier)
│   └── vca_dashboard_data.json
├── docs/
│   └── index.html                      # copie du dashboard, pour GitHub Pages
└── requirements.txt
```

## Reproduire le pipeline

```bash
pip install -r requirements.txt

# 1. Génère les données clients / transactions / points de contact
python data/generate_synthetic_data.py --n-customers 4000 --seed 42 --out-dir data

# 2. Recalcule les indicateurs et exporte le JSON du dashboard
python analysis/build_dashboard_data.py --data-dir data --out dashboard/vca_dashboard_data.json

# 3. Ouvrir dashboard/vca_client_insight_dashboard.html dans un navigateur
```

Les requêtes SQL de `sql/` sont écrites en dialecte **Google BigQuery** ; elles
sont fournies comme livrable de compétence technique (elles ciblent des tables
`client_insight.customers` / `client_insight.transactions` qu'il faudrait
charger dans un projet BigQuery pour les exécuter telles quelles). La logique
métier équivalente est réimplémentée en pandas dans `analysis/build_dashboard_data.py`,
qui est le script réellement exécuté pour produire les données du dashboard.

## Déploiement (GitHub Pages)

GitHub Pages ne sert que la racine du repo (`/`) ou un dossier `/docs` — pas un
nom de dossier arbitraire. Le dashboard est donc dupliqué dans `docs/index.html` :

1. Pousser ce repo sur GitHub.
2. Dans **Settings → Pages**, choisir *Deploy from a branch*, branche `main`, dossier **`/docs`**.
3. Le dashboard est servi à `https://<utilisateur>.github.io/<repo>/`.

Si vous régénérez les données, pensez à recopier le fichier mis à jour :
```bash
cp dashboard/vca_client_insight_dashboard.html docs/index.html
```

## Choix de conception notables

- **Harmonisation siège/marchés** : toute transaction porte un montant en
  devise locale *et* son équivalent EUR ; tous les indicateurs consolidés
  utilisent exclusivement l'EUR, sur une fenêtre de 24 mois identique pour
  tous les marchés (voir `kpi-documentation/documentation_kpis.md`, section 1).
- **CLV moyenne ET médiane** : la distribution de la dépense est très
  asymétrique en joaillerie (quelques achats Haute Joaillerie très élevés) ;
  la médiane évite de surestimer la valeur du client "typique" d'un segment.
- **RFM en complément du tier CRM**, pas à sa place : le tier reflète la
  valeur cumulée historique, le RFM le comportement récent — un client Very
  VIP inactif depuis 8 mois reste "Very VIP" dans son tier mais apparaît
  "À risque" en RFM, ce qui déclenche une action différente.
- **Design volontairement différent d'un précédent portfolio** (Air France,
  univers Ground Ops / OTP, palette marine et rouge) : ici palette ivoire /
  noir / or, typographie serif + sans-serif, ornement géométrique abstrait
  (aucun motif, logo ou photo d'une maison de joaillerie réelle).
- **Calibration sur des sources de marché publiques réelles** : la
  concentration de valeur client, le poids relatif des marchés et la part du
  canal digital ont été comparés à des rapports publics (Richemont, Bain &
  Company / Altagamma, Business of Fashion, Grand View Research) avant de
  fixer les paramètres du générateur — voir
  `kpi-documentation/documentation_kpis.md`, section 9 "Sources et
  calibration marché", pour le détail sourcé et les limites assumées.

## Fichiers liés à cette candidature

- `lettre_motivation_vca.docx` — lettre de motivation présentant ce portfolio
- `guide_preparation_entretien_vca.docx` — guide de préparation à l'entretien (process en 3 étapes)

_(livrés séparément, hors de ce repo de code)_
