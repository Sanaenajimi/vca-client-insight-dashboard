-- ============================================================================
-- Segmentation RFM (Récence / Fréquence / Montant) de la base clients
-- Dialecte : Google BigQuery Standard SQL
-- Source   : client_insight.customers, client_insight.transactions
-- ============================================================================
-- Objectif métier : au-delà du tier CRM (basé sur la dépense cumulée), la
-- segmentation RFM croise 3 dimensions pour identifier des populations
-- actionnables : clients à réactiver en urgence (forte valeur passée mais
-- récence dégradée), clients "Champions" à privilégier pour les événements
-- VIC, prospects "Prometteurs" à développer.

WITH reference_date AS (
  SELECT MAX(DATE(transaction_date)) AS today FROM `client_insight.transactions`
),

rfm_brut AS (
  SELECT
    t.customer_id,
    c.market,
    c.tier,
    DATE_DIFF((SELECT today FROM reference_date), MAX(DATE(t.transaction_date)), DAY) AS recence_jours,
    COUNT(*)                AS frequence,
    SUM(t.amount_eur)       AS montant_eur
  FROM `client_insight.transactions` AS t
  INNER JOIN `client_insight.customers` AS c
    ON c.customer_id = t.customer_id
  GROUP BY 1, 2, 3
),

rfm_scores AS (
  SELECT
    *,
    -- NTILE 5 : 5 = meilleur score (client récent / fréquent / gros montant)
    6 - NTILE(5) OVER (ORDER BY recence_jours ASC)  AS score_r,
    NTILE(5) OVER (ORDER BY frequence ASC)          AS score_f,
    NTILE(5) OVER (ORDER BY montant_eur ASC)        AS score_m
  FROM rfm_brut
),

rfm_segments AS (
  SELECT
    *,
    (score_r + score_f + score_m) AS score_rfm_total,
    CASE
      WHEN score_r >= 4 AND score_f >= 4 AND score_m >= 4 THEN "Champions"
      WHEN score_r >= 3 AND score_f >= 3                  THEN "Clients fidèles"
      WHEN score_r <= 2 AND score_f >= 3 AND score_m >= 3  THEN "À risque"
      WHEN score_r <= 2 AND score_f <= 2                   THEN "Perdus"
      WHEN score_r >= 4 AND score_f <= 2                   THEN "Prometteurs"
      ELSE "Standard"
    END AS segment_rfm
  FROM rfm_scores
)

SELECT
  market,
  segment_rfm,
  COUNT(*)                             AS nb_clients,
  ROUND(AVG(recence_jours), 0)         AS recence_moy_jours,
  ROUND(AVG(frequence), 2)             AS frequence_moy,
  ROUND(AVG(montant_eur), 0)           AS montant_moy_eur,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY market), 1) AS part_pct
FROM rfm_segments
GROUP BY market, segment_rfm
ORDER BY market, nb_clients DESC;
