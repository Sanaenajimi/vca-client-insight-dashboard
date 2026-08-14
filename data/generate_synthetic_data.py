"""
Génération d'un jeu de données clients / transactions simulé
================================================================
Simule une base clients multi-marchés d'une maison de joaillerie de luxe
(clients, transactions boutique/en ligne/événements, points de contact CRM)
sur 24 mois, pour illustrer le rôle de Data Analyst au sein d'un
département Client Insight & Data.

Ce jeu de données est 100% simulé (aucune donnée réelle d'aucune maison
de luxe) : il sert uniquement de support pédagogique / portfolio.

Usage:
    python generate_synthetic_data.py [--n-customers 4000] [--seed 42]
"""

import argparse
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

MARKETS = [
    # (marché, devise, taux -> EUR, poids population client, saisonnalité forte)
    ("France (siège)", "EUR", 1.00, 3, "decembre"),
    ("USA", "USD", 0.92, 3, "decembre"),
    ("Japon", "JPY", 0.0062, 2, "decembre"),
    ("Chine", "CNY", 0.13, 3, "nouvel_an_chinois"),
    ("Moyen-Orient", "AED", 0.25, 2, "aid"),
]

BOUTIQUES = {
    "France (siège)": ["Paris Vendôme", "Paris Champs-Élysées", "Cannes"],
    "USA": ["New York 5th Ave", "Beverly Hills", "Bal Harbour"],
    "Japon": ["Tokyo Ginza", "Osaka"],
    "Chine": ["Shanghai", "Pékin", "Hong Kong"],
    "Moyen-Orient": ["Dubaï Mall", "Abu Dhabi"],
}

CATEGORIES = [
    # (catégorie, prix moyen EUR, écart-type, poids d'occurrence)
    ("Haute Joaillerie", 85000, 45000, 1),
    ("Joaillerie", 12000, 7000, 4),
    ("Mariage", 9000, 4500, 2),
    ("Horlogerie", 22000, 11000, 2),
    ("Accessoires & Parfums", 650, 350, 5),
]

ACQUISITION_CHANNELS = ["Boutique (walk-in)", "Recommandation VIC", "Digital / en ligne", "Événement privé"]
TOUCHPOINT_TYPES = ["Rendez-vous boutique", "Appel conseiller de vente", "Événement VIC", "Ouverture newsletter", "Visite site e-commerce"]

TIER_THRESHOLDS = [
    # (tier, seuil de dépense cumulée EUR sur 24 mois)
    ("Very VIP", 220000),
    ("VIC", 65000),
    ("Client fidèle", 18000),
    ("Découverte", 0),
]


def assign_tier(total_spend_eur: float) -> str:
    for tier, threshold in TIER_THRESHOLDS:
        if total_spend_eur >= threshold:
            return tier
    return "Découverte"


def generate(n_customers: int, seed: int):
    rng = np.random.default_rng(seed)
    start_date = datetime(2024, 9, 1)
    end_date = datetime(2026, 8, 1)
    total_months = 24

    market_names = [m[0] for m in MARKETS]
    market_weights = np.array([m[3] for m in MARKETS], dtype=float)
    market_weights /= market_weights.sum()
    market_info = {m[0]: m for m in MARKETS}

    cat_names = [c[0] for c in CATEGORIES]
    cat_weights = np.array([c[3] for c in CATEGORIES], dtype=float)
    cat_weights /= cat_weights.sum()
    cat_info = {c[0]: c[1:] for c in CATEGORIES}

    customers = []
    transactions = []
    touchpoints = []

    tx_id = 0
    tp_id = 0

    for cid in range(1, n_customers + 1):
        market = rng.choice(market_names, p=market_weights)
        boutique = rng.choice(BOUTIQUES[market])
        acquisition = rng.choice(ACQUISITION_CHANNELS, p=[0.35, 0.30, 0.20, 0.15])

        # date de première interaction, répartie sur les 20 premiers mois
        # (pour laisser du temps à des cohortes plus récentes de se développer)
        join_offset_days = int(rng.integers(0, 20 * 30))
        join_date = start_date + timedelta(days=join_offset_days)

        # "affinité" latente du client : détermine sa fréquence et son panier
        affinity = rng.beta(1.3, 7.5)  # la plupart des clients ont une affinité faible, une minorité très élevée (VIC)
        is_high_value = affinity > 0.35

        # probabilité de churn mensuelle (les clients à forte affinité churnent moins)
        monthly_churn_p = float(np.clip(0.14 - affinity * 0.22, 0.015, 0.14))

        active = True
        n_tx = 0
        total_spend_eur = 0.0
        cursor = join_date
        omnichannel_used = set()

        while active and cursor < end_date:
            months_elapsed = (cursor.year - join_date.year) * 12 + (cursor.month - join_date.month)
            # rythme d'achat : plus l'affinité est forte, plus les achats sont fréquents
            base_gap_days = max(18, int(180 - affinity * 150 + rng.normal(0, 20)))
            cursor = cursor + timedelta(days=base_gap_days)
            if cursor >= end_date:
                break

            # churn check à chaque cycle
            if rng.random() < monthly_churn_p:
                active = False

            channel = rng.choice(["Boutique", "En ligne", "Événement privé"],
                                  p=[0.62, 0.28, 0.10] if not is_high_value else [0.55, 0.15, 0.30])
            omnichannel_used.add(channel)

            category = rng.choice(cat_names, p=cat_weights if not is_high_value else
                                   np.array([0.06, 0.42, 0.12, 0.22, 0.18]))
            cat_mean, cat_std, _ = cat_info[category]
            mult = 1.0 + affinity * 1.8
            amount_eur = max(150, rng.normal(cat_mean * mult, cat_std * mult * 0.5))

            # "pièce exceptionnelle" : les maisons de Haute Joaillerie vendent occasionnellement
            # des pièces uniques/sur-mesure très au-dessus du prix moyen de collection. Ce mécanisme
            # reproduit la concentration de valeur documentée dans le secteur du luxe (une minorité de
            # clients / transactions portant une part disproportionnée du chiffre d'affaires -- voir
            # kpi-documentation/documentation_kpis.md, section "Sources et calibration marché").
            piece_exceptionnelle = False
            if category == "Haute Joaillerie" and affinity > 0.30 and rng.random() < 0.12:
                amount_eur *= rng.uniform(3.0, 9.0)
                piece_exceptionnelle = True

            _, currency, fx_to_eur, _, season = market_info[market]
            # saisonnalité : pic de dépense selon le marché
            month = cursor.month
            season_boost = 1.0
            if season == "decembre" and month == 12:
                season_boost = 1.35
            if season == "nouvel_an_chinois" and month in (1, 2):
                season_boost = 1.30
            if season == "aid" and month in (4, 6):
                season_boost = 1.25
            amount_eur *= season_boost

            amount_local = amount_eur / fx_to_eur

            tx_id += 1
            transactions.append({
                "transaction_id": f"TXN{tx_id:06d}",
                "customer_id": f"CUST{cid:05d}",
                "market": market,
                "boutique": boutique,
                "channel": channel,
                "category": category,
                "transaction_date": cursor.date().isoformat(),
                "amount_local": round(amount_local, 2),
                "currency": currency,
                "amount_eur": round(amount_eur, 2),
                "piece_exceptionnelle": piece_exceptionnelle,
            })
            total_spend_eur += amount_eur
            n_tx += 1

            # 1 à 3 points de contact CRM autour de chaque achat
            for _ in range(int(rng.integers(1, 4))):
                tp_offset = int(rng.integers(-20, 5))
                tp_date = cursor + timedelta(days=tp_offset)
                if start_date <= tp_date < end_date:
                    tp_id += 1
                    touchpoints.append({
                        "touchpoint_id": f"TP{tp_id:06d}",
                        "customer_id": f"CUST{cid:05d}",
                        "touchpoint_date": tp_date.date().isoformat(),
                        "type": rng.choice(TOUCHPOINT_TYPES),
                        "market": market,
                    })

        tier = assign_tier(total_spend_eur)
        customers.append({
            "customer_id": f"CUST{cid:05d}",
            "market": market,
            "boutique_reference": boutique,
            "acquisition_channel": acquisition,
            "first_purchase_date": join_date.date().isoformat(),
            "tier": tier,
            "lifetime_transactions": n_tx,
            "lifetime_spend_eur": round(total_spend_eur, 2),
            "omnichannel": len(omnichannel_used) > 1,
            "is_active_last_6m": bool(active and n_tx > 0),
        })

    customers_df = pd.DataFrame(customers)
    transactions_df = pd.DataFrame(transactions)
    touchpoints_df = pd.DataFrame(touchpoints)
    return customers_df, transactions_df, touchpoints_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Génère un jeu de données clients/transactions simulé")
    parser.add_argument("--n-customers", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", type=str, default=".")
    args = parser.parse_args()

    customers_df, transactions_df, touchpoints_df = generate(args.n_customers, args.seed)

    customers_df.to_csv(f"{args.out_dir}/customers.csv", index=False)
    transactions_df.to_csv(f"{args.out_dir}/transactions.csv", index=False)
    touchpoints_df.to_csv(f"{args.out_dir}/touchpoints.csv", index=False)

    print(f"{len(customers_df)} clients générés -> customers.csv")
    print(f"{len(transactions_df)} transactions générées -> transactions.csv")
    print(f"{len(touchpoints_df)} points de contact CRM générés -> touchpoints.csv")
    print("\nRépartition par tier :")
    print(customers_df["tier"].value_counts())
    print("\nRépartition par marché :")
    print(customers_df["market"].value_counts())
