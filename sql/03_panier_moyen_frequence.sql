-- ============================================================================
-- Panier moyen (AOV) et fréquence d'achat, par marché et par catégorie
-- Dialecte : Google BigQuery Standard SQL
-- Source   : client_insight.transactions, client_insight.customers
-- ============================================================================
-- Objectif métier : comparer, sur une base harmonisée en euros, la valeur du
-- panier moyen et le rythme d'achat des clients selon le marché et la
-- catégorie de produit, pour orienter les actions du Client Insight (ciblage
-- CRM, allocation des stocks, plan d'animation boutique).

WITH tx_par_client AS (
  SELECT
    t.customer_id,
    t.market,
    t.category,
    COUNT(*)                    AS nb_transactions,
    SUM(t.amount_eur)           AS montant_total_eur,
    MIN(DATE(t.transaction_date)) AS premiere_transaction,
    MAX(DATE(t.transaction_date)) AS derniere_transaction
  FROM `client_insight.transactions` AS t
  GROUP BY 1, 2, 3
)

SELECT
  market,
  category,
  COUNT(DISTINCT customer_id)                                            AS nb_clients_acheteurs,
  COUNT(*)                                                               AS nb_transactions_agregees,
  ROUND(SUM(montant_total_eur) / SUM(nb_transactions), 0)                AS panier_moyen_eur,
  ROUND(AVG(nb_transactions), 2)                                         AS frequence_achat_moyenne,
  ROUND(AVG(SAFE_DIVIDE(
    DATE_DIFF(derniere_transaction, premiere_transaction, DAY),
    NULLIF(nb_transactions - 1, 0)
  )), 0)                                                                 AS delai_moyen_entre_achats_jours
FROM tx_par_client
GROUP BY market, category
ORDER BY market, panier_moyen_eur DESC;
