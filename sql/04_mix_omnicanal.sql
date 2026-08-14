-- ============================================================================
-- Mix omnicanal : clients mono-canal vs multi-canal, et poids par canal
-- Dialecte : Google BigQuery Standard SQL
-- Source   : client_insight.transactions, client_insight.customers
-- ============================================================================
-- Objectif métier : quantifier le parcours client omnicanal (boutique / en
-- ligne / événement privé) pour objectiver le lien entre multi-canal et
-- valeur client — argument clé pour les arbitrages CRM et digital.

WITH canaux_par_client AS (
  SELECT
    t.customer_id,
    t.market,
    COUNT(DISTINCT t.channel)      AS nb_canaux_utilises,
    STRING_AGG(DISTINCT t.channel, " + " ORDER BY t.channel) AS canaux,
    SUM(t.amount_eur)              AS lifetime_spend_eur
  FROM `client_insight.transactions` AS t
  GROUP BY 1, 2
),

classification AS (
  SELECT
    *,
    CASE WHEN nb_canaux_utilises > 1 THEN "Omnicanal" ELSE "Mono-canal" END AS segment_canal
  FROM canaux_par_client
)

-- Vue 1 : répartition mono-canal vs omnicanal et valeur associée
SELECT
  market,
  segment_canal,
  COUNT(*)                                        AS nb_clients,
  ROUND(AVG(lifetime_spend_eur), 0)                AS clv_moyenne_eur,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY market), 1) AS part_pct
FROM classification
GROUP BY market, segment_canal
ORDER BY market, segment_canal;

-- Vue 2 (à exécuter séparément) : poids de chaque combinaison de canaux
-- SELECT
--   market,
--   canaux,
--   COUNT(*)                          AS nb_clients,
--   ROUND(AVG(lifetime_spend_eur), 0) AS clv_moyenne_eur
-- FROM classification
-- GROUP BY market, canaux
-- ORDER BY market, nb_clients DESC;
