-- ============================================================================
-- Harmonisation siège / marchés : vue comparative des KPI's clients clés
-- Dialecte : Google BigQuery Standard SQL
-- Source   : client_insight.customers, client_insight.transactions
-- ============================================================================
-- Objectif métier : donner au siège (Client Insight & Data) une vue unique et
-- harmonisée des indicateurs clients calculés de façon homogène sur tous les
-- marchés (même devise de référence EUR, mêmes définitions de tier et de
-- fenêtre temporelle), pour fiabiliser les comparaisons et le reporting
-- consolidé remonté aux marchés.

WITH base_client AS (
  SELECT
    c.customer_id,
    c.market,
    c.tier,
    c.acquisition_channel,
    c.omnichannel,
    c.is_active_last_6m,
    COALESCE(SUM(t.amount_eur), 0) AS lifetime_spend_eur,
    COUNT(t.transaction_id)        AS lifetime_transactions
  FROM `client_insight.customers` AS c
  LEFT JOIN `client_insight.transactions` AS t
    ON t.customer_id = c.customer_id
  GROUP BY 1, 2, 3, 4, 5, 6
)

SELECT
  market,
  COUNT(*)                                                              AS nb_clients_total,
  ROUND(AVG(lifetime_spend_eur), 0)                                     AS clv_moyenne_eur,
  ROUND(100 * SUM(IF(tier IN ("Very VIP", "VIC"), 1, 0)) / COUNT(*), 1) AS part_vic_pct,
  ROUND(100 * SUM(IF(omnichannel, 1, 0)) / COUNT(*), 1)                 AS part_omnicanal_pct,
  ROUND(100 * SUM(IF(is_active_last_6m, 1, 0)) / COUNT(*), 1)           AS taux_actifs_pct,
  ROUND(100 * SUM(IF(acquisition_channel = "Digital / en ligne", 1, 0)) / COUNT(*), 1) AS part_acquisition_digitale_pct,
  ROUND(AVG(lifetime_transactions), 2)                                  AS transactions_moyennes_par_client
FROM base_client
GROUP BY market
ORDER BY clv_moyenne_eur DESC;
