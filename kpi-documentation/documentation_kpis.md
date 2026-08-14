# Documentation des indicateurs — Client Insight & Data

Ce document définit chaque indicateur du dashboard : sa formule, sa source, son
objectif métier, et surtout **la façon dont il est harmonisé entre le siège et
les marchés** — un des enjeux centraux du poste (« veiller à l'harmonisation
des définitions et du reporting entre le siège et les marchés »).

Toutes les données sont **100% simulées** (aucune donnée réelle d'aucune maison
de luxe) : ce projet est un support de portfolio, pas un audit d'une entreprise
existante.

---

## 1. Principe d'harmonisation

Le problème que ce document adresse : sans définition centrale, chaque marché a
tendance à calculer ses propres indicateurs dans sa propre devise, sur sa
propre fenêtre temporelle, avec sa propre définition de « client actif » — ce
qui rend toute comparaison ou consolidation trompeuse.

Trois règles simples, appliquées uniformément à tous les marchés dans ce
projet :

1. **Devise de référence unique.** Toute transaction est stockée avec son
   montant en devise locale (`amount_local`) **et** son équivalent en euros
   (`amount_eur`), calculé avec un taux de change fixe et documenté. Tous les
   indicateurs consolidés (CLV, panier moyen, etc.) utilisent `amount_eur`,
   jamais un mélange de devises.
2. **Fenêtre d'observation commune.** Tous les indicateurs de cycle de vie
   (CLV, rétention, fréquence) sont calculés sur la même profondeur d'historique
   (24 mois glissants) pour tous les marchés, plutôt que sur des périodes
   fiscales ou calendaires différentes selon le pays.
3. **Définitions uniques, appliquées globalement.** Un client « actif » est un
   client ayant réalisé au moins un achat dans les 6 derniers mois, quel que
   soit le marché. Un client « omnicanal » est un client ayant utilisé plus
   d'un canal d'achat sur la période, avec la même liste de canaux
   (Boutique / En ligne / Événement privé) pour tous les marchés.

---

## 2. CLV — Customer Lifetime Value

| | |
|---|---|
| **Définition** | Somme des montants de toutes les transactions d'un client (en EUR), depuis sa première visite. |
| **Formule** | `CLV = Σ amount_eur` pour toutes les transactions du client |
| **Granularité restituée** | Moyenne et médiane, par marché et par tier CRM |
| **Pourquoi la médiane en plus de la moyenne** | La distribution de la dépense est très asymétrique (quelques clients Haute Joaillerie très au-dessus de la masse) : la moyenne seule surestime la valeur du client « typique ». La médiane donne une vision plus réaliste du client médian de chaque segment. |
| **Usage métier** | Prioriser les segments à fort potentiel pour les actions de fidélisation VIC ; objectiver les écarts de valeur entre marchés pour le siège. |
| **Fichier source** | `sql/01_clv_par_marche_tier.sql`, `analysis/build_dashboard_data.py::build_clv_par_marche_tier` |

### Tiers CRM (segmentation par dépense cumulée sur 24 mois)

| Tier | Seuil de dépense cumulée |
|---|---|
| Very VIP | ≥ 220 000 € |
| VIC | ≥ 65 000 € |
| Client fidèle | ≥ 18 000 € |
| Découverte | < 18 000 € |

---

## 3. Rétention & analyse de cohortes

| | |
|---|---|
| **Définition** | Part des clients d'une cohorte d'acquisition (mois de première transaction) encore actifs N mois plus tard. |
| **Formule** | `Rétention(mois N) = nb clients actifs au mois N / nb clients de la cohorte` |
| **Granularité restituée** | Courbe agrégée tous marchés (mois 0 à 12), et matrice détaillée cohort_month × month_number disponible en SQL |
| **Pourquoi ce n'est pas la même chose que le taux d'attrition (churn)** | Le churn mesure un flux global sur une période donnée (combien de clients ont cessé d'acheter ce mois-ci) ; la rétention par cohorte isole l'effet du temps écoulé depuis l'acquisition, ce qui permet de répondre à une question différente et plus actionnable : « un client acquis via tel canal, à telle période, reste-t-il fidèle plus longtemps ? » |
| **Lecture attendue** | Dans l'univers de la haute joaillerie, le cycle d'achat est long (occasions, cadeaux, anniversaires) : une courbe de rétention irrégulière (pics à 5-6 mois, 11-12 mois) est cohérente avec des achats calés sur des événements plutôt que sur un rythme mensuel régulier — contrairement à un e-commerce de grande consommation. |
| **Fichier source** | `sql/02_retention_cohortes.sql`, `analysis/build_dashboard_data.py::build_cohortes` |

---

## 4. Panier moyen (AOV) & fréquence d'achat

| | |
|---|---|
| **Définition** | Montant moyen par transaction (AOV), et nombre moyen de transactions par client, par catégorie de produit. |
| **Formule** | `AOV = Σ montant transactions / nb transactions` ; `Fréquence = nb transactions / nb clients acheteurs` |
| **Granularité restituée** | Par catégorie (Haute Joaillerie, Joaillerie, Mariage, Horlogerie, Accessoires & Parfums) |
| **Usage métier** | Piloter le mix produit et le merchandising ; anticiper les besoins de stock par catégorie et par marché ; mesurer l'effet des collections/lancements sur la fréquence. |
| **Fichier source** | `sql/03_panier_moyen_frequence.sql`, `analysis/build_dashboard_data.py::build_aov_frequence` |

---

## 5. Mix omnicanal

| | |
|---|---|
| **Définition** | Répartition des clients entre mono-canal (un seul canal d'achat utilisé) et omnicanal (plusieurs canaux), et écart de valeur (CLV) associé. |
| **Formule** | `nb_canaux_distincts(client) > 1` → Omnicanal, sinon Mono-canal |
| **Résultat observé (données simulées)** | Les clients omnicanaux ont une CLV moyenne environ **2 fois supérieure** aux clients mono-canal, de façon homogène sur les 5 marchés. |
| **Usage métier** | Argumenter en faveur des investissements permettant le passage au multi-canal (continuité boutique ↔ digital ↔ événementiel) plutôt que d'opposer les canaux entre eux. |
| **Fichier source** | `sql/04_mix_omnicanal.sql`, `analysis/build_dashboard_data.py::build_mix_omnicanal` |

---

## 6. Harmonisation siège / marchés

| | |
|---|---|
| **Définition** | Vue comparative, marché par marché, des indicateurs clés calculés avec une définition strictement identique (voir section 1). |
| **Indicateurs comparés** | Nombre de clients, CLV moyenne, part de clients VIC/Very VIP, part omnicanale, taux d'actifs à 6 mois, part d'acquisition digitale |
| **Usage métier** | C'est la vue que consulte le siège pour arbitrer entre marchés sans biais méthodologique — l'écart observé reflète une différence réelle de comportement client, pas une différence de calcul. |
| **Fichier source** | `sql/05_harmonisation_marches.sql`, `analysis/build_dashboard_data.py::build_harmonisation_marches` |

---

## 7. Segmentation RFM (Récence / Fréquence / Montant)

| | |
|---|---|
| **Définition** | Segmentation croisant 3 dimensions comportementales, calculées en quintiles (score 1 à 5 sur chaque axe) : Récence (temps depuis le dernier achat), Fréquence (nombre d'achats), Montant (dépense totale). |
| **Différence avec le tier CRM** | Le tier CRM reflète la valeur **cumulée historique** du client (utile pour le service, les avantages boutique). Le RFM reflète le comportement **récent** du client et permet de détecter des signaux que le tier seul ne voit pas : un client Very VIP qui n'a rien acheté depuis 8 mois reste "Very VIP" dans son tier, mais apparaît en "À risque" dans le RFM — ce qui déclenche une action différente. |
| **Segments et actions associées** | Voir tableau ci-dessous |
| **Fichier source** | `sql/06_segmentation_rfm.sql`, `analysis/build_dashboard_data.py::build_rfm` |

### Segments RFM et recommandations d'action

| Segment | Profil | Action CRM suggérée |
|---|---|---|
| **Champions** | Récent, fréquent, gros montant | Programme VIC, invitations événements privés en priorité |
| **Clients fidèles** | Récent, régulier | Entretenir la relation conseiller de vente, avant-premières collections |
| **À risque** | Ancien montant élevé, mais récence dégradée | Ré-engagement prioritaire — contact personnalisé du conseiller référent |
| **Prometteurs** | Récent, mais peu fréquent encore | Développer la relation, deuxième achat facilité |
| **Perdus** | Ni récent, ni fréquent | Campagne de réactivation à faible coût, ou désinvestissement |
| **Standard** | Ne correspond à aucun profil marqué | Suivi standard |

---

## 8. Points de contact CRM (touchpoints)

| | |
|---|---|
| **Définition** | Répartition des interactions clients par type (rendez-vous boutique, appel conseiller, événement VIC, newsletter, visite site). |
| **Usage métier** | Vérifier l'équilibre entre canaux de sollicitation et détecter une sur- ou sous-sollicitation d'un segment. |
| **Fichier source** | `analysis/build_dashboard_data.py::build_touchpoints_summary` |

---

## 9. Sources et calibration marché

Les paramètres du générateur (`data/generate_synthetic_data.py`) ne sont pas
choisis arbitrairement : chaque hypothèse structurante a été comparée à des
données de marché publiques (études sectorielles, rapports annuels de groupes
de luxe cotés, presse spécialisée) avant d'être fixée. Aucune de ces sources
ne documente les chiffres internes d'une maison en particulier — ce ne sont
pas des données confidentielles — mais elles donnent des ordres de grandeur
crédibles pour calibrer un jeu de données synthétique.

| Hypothèse du projet | Source | Ce que dit la source | Calibration retenue |
|---|---|---|---|
| Concentration de la valeur client | [Business of Fashion — "How Luxury Brands Court the 1 Percent"](https://www.businessoffashion.com/articles/luxury/how-luxury-brands-court-the-1-percent/) | Chez Mytheresa (e-commerce multi-marques de luxe), 3 % des clients génèrent 30 % du chiffre d'affaires ; selon Gary Wassner (Hilldun Group), les gros clients fidèles peuvent porter jusqu'à 40 % des ventes d'une maison de luxe. | Ajout d'un mécanisme de "pièces exceptionnelles" (achats rares, 3 à 9 fois le prix moyen de collection, réservés aux clients à forte affinité en Haute Joaillerie) : sur les données générées, les 3 % de clients les plus importants portent ~20-23 % du chiffre d'affaires simulé, et les tiers VIC + Very VIP (17 % des clients) en portent ~60 %. Directionnellement cohérent, sans viser une réplique exacte d'un cas particulier — Mytheresa est un modèle d'affaires différent (revendeur multi-marques) d'une maison mono-marque avec CRM boutique. |
| Répartition et dynamique des 5 marchés | [Richemont — Résultats annuels FY25 (année close au 31 mars 2025)](https://www.richemont.com/news-media/press-releases-news/richemont-posts-robust-performance-for-the-year-ended-31-march-2025/) | Le segment Jewellery Maisons (Cartier, Van Cleef & Arpels) affiche +8 % de croissance sur l'exercice, avec de fortes disparités régionales : Amériques +16 %, Europe +10 %, Moyen-Orient & Afrique +15 %, **Japon +25 %** (le plus fort, porté par la clientèle touristique et un yen faible), **Asie-Pacifique -13 %** (Chine/Hong Kong/Macau en repli). | Confirme que les 5 marchés retenus (France siège, USA, Japon, Chine, Moyen-Orient) sont pertinents et que leur poids relatif dans le projet (France/USA/Chine plus grands, Japon/Moyen-Orient plus petits) reste plausible. **Limite assumée** : ce projet simule une photographie figée sur 24 mois, pas une tendance de croissance — il ne capture donc pas le retournement récent Japon ↑ / Chine ↓ observé dans la réalité 2024-2025. |
| Marché mondial de la bijouterie — taille et canal | [Grand View Research — Jewelry Market Report](https://www.grandviewresearch.com/industry-analysis/jewelry-market) | Marché mondial estimé à 381,5 Md$ en 2025 ; répartition régionale Asie-Pacifique 60,4 %, Amérique du Nord 22,2 % ; distribution 83,9 % en magasin contre une croissance du canal en ligne à 8 % CAGR (implicitement ~16 % de part en ligne aujourd'hui). | Utilisé pour vérifier que la part d'acquisition digitale du projet (18-21 % selon les marchés) et la part omnicanale (~38 %) restent dans un ordre de grandeur cohérent avec un secteur encore majoritairement physique. **Limite assumée** : cette étude couvre l'ensemble du marché de la bijouterie (y compris bijouterie grand public, plus digitalisée), alors que la Très Haute Joaillerie reste structurellement plus dépendante du contact humain en boutique — le projet ne distingue pas ce niveau de granularité par catégorie. |
| Contexte marché du luxe 2025 | [Bain & Company / Altagamma — Global luxury stays resilient... (2025)](https://www.bain.com/about/media-center/press-releases/20252/global-luxury-stays-resilient-despite-economic-headwinds-and-shifting-consumer-trends-that-reshape-marketbain--company-and-altagamma/) | Marché des biens de luxe personnels estimé à 364 Md€ en 2024, en repli à 358 Md€ en 2025 (-2 %) ; base de consommateurs de luxe en baisse (400M en 2022 → ~340M en 2025) ; acheteurs actifs en baisse (~60 % de la base adressable en 2022 → 40-45 % en 2025) ; acquisition de nouveaux clients en baisse de 5 % sur un an. | **Non intégré directement** au générateur : ce projet modélise une base de clients déjà acquis (taux d'actifs à 6 mois ~70 %), une mesure différente du taux de pénétration du marché total mesuré par Bain. Mentionné ici pour transparence — un vrai projet en production croiserait ces deux niveaux de lecture (marché total vs base CRM propriétaire). |

**Pourquoi documenter cela plutôt que de simplement ajuster les chiffres en
silence :** en entretien comme en poste, la vraie compétence n'est pas de
produire un chiffre qui « sonne juste », mais de savoir dire précisément sur
quoi une hypothèse s'appuie, et où s'arrêtent ses limites. C'est cette
posture — plutôt que l'exactitude des chiffres eux-mêmes, impossible à
garantir sur des données simulées — qui est le vrai objet de cette section.

## 10. Limites et hypothèses assumées

- Les taux de change utilisés sont **fixes** (illustratifs), alors qu'en
  production ils seraient historisés à la date de transaction — précisé pour
  ne pas induire en erreur sur la méthodologie réelle recommandée.
- La rétention est calculée par cohorte mensuelle agrégée sur 24 mois
  d'historique simulé, une profondeur volontairement limitée pour un exercice
  de portfolio ; en production, une fenêtre de 36+ mois serait recommandée
  pour la haute joaillerie compte tenu du cycle d'achat long.
- Les seuils de tier CRM et les paramètres de génération (affinité client) sont
  calibrés pour produire une pyramide de valeur réaliste (majorité de clients
  « Découverte », minorité « Very VIP ») mais restent arbitraires et
  pédagogiques.
