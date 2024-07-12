WITH cco AS (
    SELECT *
    FROM d2dbanking_core_cco_operacao_bancaria_em_efetivada_old
    WHERE ingestionTime >= ToDateTime(ago('P4DT3H'), 'yyyy-MM-dd hh:mm:ss')
),
eb AS (
    SELECT *
    FROM d2dbanking_core_eb_operacao_bancaria_em_efetivada_old
    WHERE ingestionTime >= ToDateTime(ago('P4DT3H'), 'yyyy-MM-dd hh:mm:ss')
),
cc AS (
    SELECT *
    FROM d2dbanking_core_cc_operacao_bancaria_em_efetivada_old
    WHERE ingestionTime >= ToDateTime(ago('P4DT3H'), 'yyyy-MM-dd hh:mm:ss')
)
SELECT 
    'Entrada de Movimento' AS "funcionalidade",
    cco.idArchSagaOperation AS "cco_idArchSagaOperation",
    cco.movimento_valorMovimento AS "cco_movimento_valorMovimento",
    eb.idArchSagaOperation AS "eb_idArchSagaOperation",
    eb.movimento_valorMovimento AS "eb_movimento_valorMovimento",
    cc.idArchSagaOperation AS "cc_idArchSagaOperation",
    cc.movimento_valorMovimento AS "cc_movimento_valorMovimento",
    cco.movimento_dataContabil_ts AS "cco_movimento_dataContabil_ts",
    cco.movimento_dataHoraInclusao_ts AS "cco_movimento_dataHoraInclusao_ts",
    cco.ingestionTime AS "cco_ingestionTime",
    eb.ingestionTime AS "eb_ingestionTime",
    cc.ingestionTime AS "cc_ingestionTime"
FROM cco
LEFT JOIN eb 
    ON cco.idArchSagaOperation = eb.idArchSagaOperation
    AND cco.cdColigada = eb.cdColigada
    AND cco.cdAgencia = eb.cdAgencia
    AND CAST(cco.nuConta AS BIGINT) = CAST(eb.nuConta AS BIGINT)
LEFT JOIN cc 
    ON cco.idArchSagaOperation = cc.idArchSagaOperation
    AND cco.cdColigada = cc.cdColigada
    AND cco.cdAgencia = cc.cdAgencia
    AND CAST(cco.nuConta AS BIGINT) = CAST(cc.nuConta AS BIGINT)
WHERE cco.flContaMigrada = 'S'
AND cco.ingestionTime BETWEEN ToDateTime(ago('P4DT3H5M'), 'yyyy-MM-dd hh:mm:ss') 
AND ToDateTime(ago('PT5M'), 'yyyy-MM-dd hh:mm:ss')
AND funcionalidade <> 'Transferência Crédito'
AND (TIMECONVERT(cco_movimento_dataContabil_ts, 'milliseconds', 'milliseconds') < ago('PT5M'))
