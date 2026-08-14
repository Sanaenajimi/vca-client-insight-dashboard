"""
Analyse Client Insight & Data — construction du jeu de données du dashboard
============================================================================
Reprend en pandas la même logique métier que les requêtes SQL BigQuery du
dossier /sql (CLV, rétention par cohorte, panier moyen, mix omnicanal,
harmonisation marchés, segmentation RFM), et exporte un unique fichier JSON
consommé par le dashboard HTML.

Usage:
    python build_dashboard_data.py --data-dir ../data --out ../dashboard/vca_dashboard_data.json
"""

import argparse
import json
from datetime import datetime

import numpy as np
import pandas as pd

TIER_ORDER = ["Découverte", "Client fidèle", "VIC", "Very VIP"]
MARKET_ORDER = ["France (siège)", "USA", "Japon", "Chine", "Moyen-Orient"]
CATEGORY_ORDER = ["Haute Joaillerie", "Horlogerie", "Joaillerie", "Mariage", "Accessoires & Parfums"]


def load_data(data_dir: str):
    customers = pd.read_csv(f"{data_dir}/customers.csv", parse_dates=["first_purchase_date"])
    transactions = pd.read_csv(f"{data_dir}/transactions.csv", parse_dates=["transaction_date"])
    touchpoints = pd.read_csv(f"{data_dir}/touchpoints.csv", parse_dates=["touchpoint_date"])
    return customers, transactions, touchpoints


def build_overview(customers, transactions):
    spend_by_customer = transactions.groupby("customer_id")["amount_eur"].sum()
    clv_moyenne = spend_by_customer.reindex(customers["customer_id"]).fillna(0).mean()
    part_omni = customers["omnichannel"].mean() * 100
    taux_actif = customers["is_active_last_6m"].mean() * 100
    part_vic = customers["tier"].isin(["VIC", "Very VIP"]).mean() * 100
    return {
        "nb_clients": int(len(customers)),
        "nb_transactions": int(len(transactions)),
        "nb_marches": int(customers["market"].nunique()),
        "clv_moyenne_eur": round(float(clv_moyenne), 0),
        "part_omnicanal_pct": round(float(part_omni), 1),
        "taux_actifs_6m_pct": round(float(taux_actif), 1),
        "part_vic_pct": round(float(part_vic), 1),
        "montant_total_eur": round(float(transactions["amount_eur"].sum()), 0),
    }


def build_clv_par_marche_tier(customers, transactions):
    # customers.csv contient déjà lifetime_spend_eur / lifetime_transactions
    # (calculés à la génération) — on les réutilise directement, comme le
    # ferait la requête SQL équivalente sur la table customers.
    merged = customers.set_index("customer_id")
    rows = []
    for market in MARKET_ORDER:
        for tier in TIER_ORDER:
            subset = merged[(merged["market"] == market) & (merged["tier"] == tier)]
            if len(subset) == 0:
                continue
            rows.append({
                "market": market,
                "tier": tier,
                "nb_clients": int(len(subset)),
                "clv_moyenne_eur": round(float(subset["lifetime_spend_eur"].mean()), 0),
                "clv_mediane_eur": round(float(subset["lifetime_spend_eur"].median()), 0),
                "transactions_moyennes": round(float(subset["lifetime_transactions"].mean()), 1),
            })
    return rows


def build_harmonisation_marches(customers, transactions):
    merged = customers.set_index("customer_id")
    rows = []
    for market in MARKET_ORDER:
        sub = merged[merged["market"] == market]
        rows.append({
            "market": market,
            "nb_clients": int(len(sub)),
            "clv_moyenne_eur": round(float(sub["lifetime_spend_eur"].mean()), 0),
            "part_vic_pct": round(float(sub["tier"].isin(["VIC", "Very VIP"]).mean() * 100), 1),
            "part_omnicanal_pct": round(float(sub["omnichannel"].mean() * 100), 1),
            "taux_actifs_pct": round(float(sub["is_active_last_6m"].mean() * 100), 1),
            "part_acquisition_digitale_pct": round(float((sub["acquisition_channel"] == "Digital / en ligne").mean() * 100), 1),
            "transactions_moyennes": round(float(sub["lifetime_transactions"].mean()), 2),
        })
    return sorted(rows, key=lambda r: r["clv_moyenne_eur"], reverse=True)


def build_mix_omnicanal(transactions):
    canaux = transactions.groupby(["customer_id", "market"]).agg(
        nb_canaux=("channel", "nunique"),
        spend=("amount_eur", "sum"),
    ).reset_index()
    canaux["segment"] = np.where(canaux["nb_canaux"] > 1, "Omnicanal", "Mono-canal")
    rows = []
    for market in MARKET_ORDER:
        for segment in ["Mono-canal", "Omnicanal"]:
            sub = canaux[(canaux["market"] == market) & (canaux["segment"] == segment)]
            if len(sub) == 0:
                continue
            rows.append({
                "market": market,
                "segment": segment,
                "nb_clients": int(len(sub)),
                "clv_moyenne_eur": round(float(sub["spend"].mean()), 0),
            })
    return rows


def build_aov_frequence(transactions):
    tx = transactions.groupby(["market", "category", "customer_id"]).agg(
        nb_tx=("transaction_id", "count"),
        montant=("amount_eur", "sum"),
    ).reset_index()
    rows = []
    for category in CATEGORY_ORDER:
        sub = tx[tx["category"] == category]
        rows.append({
            "category": category,
            "nb_clients_acheteurs": int(sub["customer_id"].nunique()),
            "panier_moyen_eur": round(float(sub["montant"].sum() / sub["nb_tx"].sum()), 0),
            "frequence_moyenne": round(float(sub["nb_tx"].mean()), 2),
        })
    return sorted(rows, key=lambda r: r["panier_moyen_eur"], reverse=True)


def build_cohortes(customers, transactions):
    fp = customers[["customer_id", "market"]].copy()
    fp["cohort_month"] = customers["first_purchase_date"].dt.to_period("M")

    cm = transactions[["customer_id"]].copy()
    cm["activity_month"] = transactions["transaction_date"].dt.to_period("M")
    cm = cm.drop_duplicates()

    merged = fp.merge(cm, on="customer_id")
    merged = merged[merged["activity_month"] >= merged["cohort_month"]]
    merged["month_number"] = (
        (merged["activity_month"].dt.year - merged["cohort_month"].dt.year) * 12
        + (merged["activity_month"].dt.month - merged["cohort_month"].dt.month)
    )
    merged = merged[(merged["month_number"] >= 0) & (merged["month_number"] <= 12)]

    cohort_size = fp.groupby("cohort_month")["customer_id"].nunique()

    # Matrice agrégée tous marchés confondus : month_number -> % rétention moyen
    activity = merged.groupby(["cohort_month", "month_number"])["customer_id"].nunique().reset_index()
    activity["cohort_size"] = activity["cohort_month"].map(cohort_size)
    activity["retention_pct"] = activity["customer_id"] / activity["cohort_size"] * 100

    avg_by_month = activity.groupby("month_number")["retention_pct"].mean().round(1)
    curve = [{"month_number": int(m), "retention_pct": float(v)} for m, v in avg_by_month.items()]
    curve.sort(key=lambda r: r["month_number"])

    # taux de rétention à 12 mois (indicateur de synthèse)
    ret_12m = float(avg_by_month.get(12, np.nan))
    return curve, (round(ret_12m, 1) if not np.isnan(ret_12m) else None)


def build_rfm(customers, transactions):
    ref_date = transactions["transaction_date"].max()
    rfm = transactions.groupby("customer_id").agg(
        derniere_transaction=("transaction_date", "max"),
        frequence=("transaction_id", "count"),
        montant=("amount_eur", "sum"),
    )
    rfm["recence_jours"] = (ref_date - rfm["derniere_transaction"]).dt.days
    rfm["market"] = customers.set_index("customer_id")["market"]

    rfm["score_r"] = 6 - pd.qcut(rfm["recence_jours"], 5, labels=False, duplicates="drop") - 1
    rfm["score_f"] = pd.qcut(rfm["frequence"].rank(method="first"), 5, labels=False, duplicates="drop") + 1
    rfm["score_m"] = pd.qcut(rfm["montant"], 5, labels=False, duplicates="drop") + 1

    def segment(row):
        r, f, m = row["score_r"], row["score_f"], row["score_m"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if r >= 3 and f >= 3:
            return "Clients fidèles"
        if r <= 2 and f >= 3 and m >= 3:
            return "À risque"
        if r <= 2 and f <= 2:
            return "Perdus"
        if r >= 4 and f <= 2:
            return "Prometteurs"
        return "Standard"

    rfm["segment_rfm"] = rfm.apply(segment, axis=1)
    summary = rfm.groupby("segment_rfm").agg(
        nb_clients=("segment_rfm", "count"),
        montant_moyen_eur=("montant", "mean"),
        recence_moyenne_jours=("recence_jours", "mean"),
        frequence_moyenne=("frequence", "mean"),
    ).reset_index()

    order = ["Champions", "Clients fidèles", "Prometteurs", "Standard", "À risque", "Perdus"]
    summary["sort_key"] = summary["segment_rfm"].apply(lambda s: order.index(s) if s in order else 99)
    summary = summary.sort_values("sort_key").drop(columns="sort_key")

    rows = []
    for _, row in summary.iterrows():
        rows.append({
            "segment": row["segment_rfm"],
            "nb_clients": int(row["nb_clients"]),
            "montant_moyen_eur": round(float(row["montant_moyen_eur"]), 0),
            "recence_moyenne_jours": round(float(row["recence_moyenne_jours"]), 0),
            "frequence_moyenne": round(float(row["frequence_moyenne"]), 2),
        })
    return rows


def build_touchpoints_summary(touchpoints):
    counts = touchpoints["type"].value_counts().reset_index()
    counts.columns = ["type", "nb"]
    total = counts["nb"].sum()
    counts["part_pct"] = (counts["nb"] / total * 100).round(1)
    return counts.to_dict(orient="records")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="../data")
    parser.add_argument("--out", default="../dashboard/vca_dashboard_data.json")
    args = parser.parse_args()

    customers, transactions, touchpoints = load_data(args.data_dir)

    cohort_curve, retention_12m = build_cohortes(customers, transactions)

    data = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overview": {
            **build_overview(customers, transactions),
            "taux_retention_12m_pct": retention_12m,
        },
        "clv_par_marche_tier": build_clv_par_marche_tier(customers, transactions),
        "harmonisation_marches": build_harmonisation_marches(customers, transactions),
        "mix_omnicanal": build_mix_omnicanal(transactions),
        "aov_frequence": build_aov_frequence(transactions),
        "cohortes_retention": cohort_curve,
        "rfm_segments": build_rfm(customers, transactions),
        "touchpoints_summary": build_touchpoints_summary(touchpoints),
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Export -> {args.out}")
    print(f"Overview: {json.dumps(data['overview'], ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()
