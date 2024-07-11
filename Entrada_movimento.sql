SELECT 
    day(ingestionTime) AS days, 
    COUNT(*) 
FROM 
    d2dbanking_core_cco_operacao_bancaria_em_efetivada_old 
WHERE 
    ingestionTime >= ToDateTime(DATETRUNC('day', CURRENT_TIMESTAMP) - INTERVAL '4' DAY, 'yyyy-MM-dd HH:mm:ss') 
    AND ingestionTime < ToDateTime(CURRENT_TIMESTAMP - INTERVAL '5' MINUTE, 'yyyy-MM-dd HH:mm:ss') 
GROUP BY 
    days
