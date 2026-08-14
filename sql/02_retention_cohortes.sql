-- ============================================================================
-- Rétention par cohorte d'acquisition (mois de première transaction)
-- Dialecte : Google BigQuery Standard SQL
-- Source   : client_insight.customers, client_insight.transactions
-- ============================================================================
-- Objectif métier : mesurer la fidélisation réelle des clients dans le temps,
-- au-delà du taux d'attrition global, en suivant chaque cohorte mensuelle
-- d'acquisition et sa part de clients encore actifs mois après mois. Sert de
-- base au reporting de rétention harmonisé siège / marchés.

WITH first_purchase AS (
  SELECT
    customer_id,
    market,
    DATE_TRUNC(DATE(first_purchase_date), MONTH) AS cohort_month
  FROM `client_insight.customers`
),

customer_months AS (
  -- Chaque mois calendaire où le client a réalisé au moins une transaction
  SELECT DISTINCT
    t.customer_id,
    DATE_TRUNC(DATE(t.transaction_date), MONTH) AS activity_month
  FROM `client_insight.transactions` AS t
),

cohort_activity AS (
  SELECT
    fp.market,
    fp.cohort_month,
    fp.customer_id,
    cm.activity_month,
    DATE_DIFF(cm.activity_month, fp.cohort_month, MONTH) AS month_number
  FROM first_purchase AS fp
  INNER JOIN customer_months AS cm
    ON cm.customer_id = fp.customer_id
  WHERE cm.activity_month >= fp.cohort_month
),

cohort_size AS (
  SELECT
    market,
    cohort_month,
    COUNT(DISTINCT customer_id) AS nb_clients_cohorte
  FROM first_purchase
  GROUP BY 1, 2
)

-- Matrice de rétention : cohort_month x month_number -> % de clients actifs
SELECT
  ca.market,
  ca.cohort_month,
  cs.nb_clients_cohorte,
  ca.month_number,
  COUNT(DISTINCT ca.customer_id)                                            AS nb_clients_actifs,
  ROUND(SAFE_DIVIDE(COUNT(DISTINCT ca.customer_id), cs.nb_clients_cohorte) * 100, 1) AS taux_retention_pct
FROM cohort_activity AS ca
INNER JOIN cohort_size AS cs
  ON cs.market = ca.market AND cs.cohort_month = ca.cohort_month
WHERE ca.month_number BETWEEN 0 AND 12
GROUP BY ca.market, ca.cohort_month, cs.nb_clients_cohorte, ca.month_number
ORDER BY ca.market, ca.cohort_month, ca.month_number;
