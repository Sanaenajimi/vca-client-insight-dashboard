-- ============================================================================
-- CLV (Customer Lifetime Value) moyenne et médiane, par marché et par tier CRM
-- Dialecte : Google BigQuery Standard SQL
-- Source   : client_insight.customers, client_insight.transactions
-- ============================================================================
-- Objectif métier : donner une vision harmonisée de la valeur client entre le
-- siège et les marchés, en s'appuyant sur une définition unique de la CLV
-- (somme des transactions EUR sur toute la relation client) plutôt que sur des
-- calculs propres à chaque marché.

WITH customer_spend AS (
  SELECT
    c.customer_id,
    c.market,
    c.tier,
    c.first_purchase_date,
    COALESCE(SUM(t.amount_eur), 0)      AS lifetime_spend_eur,
    COUNT(t.transaction_id)             AS lifetime_transactions
  FROM `client_insight.customers` AS c
  LEFT JOIN `client_insight.transactions` AS t
    ON t.customer_id = c.customer_id
  GROUP BY 1, 2, 3, 4
)

SELECT
  market,
  tier,
  COUNT(*)                                                     AS nb_clients,
  ROUND(AVG(lifetime_spend_eur), 0)                            AS clv_moyenne_eur,
  ROUND(APPROX_QUANTILES(lifetime_spend_eur, 2)[OFFSET(1)], 0) AS clv_mediane_eur,
  ROUND(AVG(lifetime_transactions), 1)                         AS transactions_moyennes_par_client
FROM customer_spend
GROUP BY market, tier
ORDER BY market, clv_moyenne_eur DESC;
