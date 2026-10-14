-- Warehouse de NovaPay: del envío de las hojas de cálculo al informe de liquidez.

-- Staging: importes interpretados (también los escritos como texto en formato español),
-- signo según el lado del balance y una sola fila por partida, unidad y día.
-- Sin CTE: una sola SELECT por tabla para que el linaje del capítulo 7 llegue hasta raw.
CREATE OR REPLACE TABLE staging.stg_liquidity_items AS
SELECT
    report_date || '|' || business_unit || '|' || item AS item_key,
    CAST(report_date AS DATE) AS report_date,
    business_unit,
    item,
    any_value(submitted_by) AS submitted_by,
    max(abs(CASE
        WHEN amount LIKE '%,%' THEN CAST(replace(replace(amount, '.', ''), ',', '.') AS DOUBLE)
        ELSE TRY_CAST(amount AS DOUBLE)
    END)) AS amount,
    count(*) AS submissions
FROM raw.liquidity_submissions
GROUP BY report_date, business_unit, item;

CREATE OR REPLACE TABLE staging.stg_accounts AS
SELECT account_id, holder_name, iban, phone, kyc_status,
       CAST(opened_at AS DATE) AS opened_at
FROM raw.accounts;

-- Curated: el informe de liquidez diario. Si falta algún importe, el día queda incompleto:
-- no se calcula la ratio (no se inventa el dato) y se pide el reenvío a la unidad.
CREATE OR REPLACE TABLE curated.fct_liquidity_report AS
SELECT
    i.report_date,
    sum(CASE WHEN u.side = 'asset' THEN i.amount END) AS liquid_assets,
    sum(CASE WHEN u.side = 'liability' THEN i.amount END) AS short_term_liabilities,
    CASE WHEN count(*) FILTER (WHERE i.amount IS NULL) = 0
        THEN sum(CASE WHEN u.side = 'asset' THEN i.amount END)
             / sum(CASE WHEN u.side = 'liability' THEN i.amount END)
    END AS liquidity_ratio,
    count(*) FILTER (WHERE i.amount IS NULL) AS missing_items,
    count(*) FILTER (WHERE i.amount IS NULL) = 0 AS complete
FROM staging.stg_liquidity_items AS i
JOIN raw.business_units AS u ON u.business_unit = i.business_unit
GROUP BY i.report_date;
