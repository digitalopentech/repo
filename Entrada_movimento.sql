SELECT 
    day(ingestionTime) AS days, 
    count(1) 
FROM 
    d2dbanking_core_cco_operacao_bancaria_em_efetivada_old 
WHERE 
    ingestionTime BETWEEN ToDateTime(now() - INTERVAL '3' DAY - INTERVAL '5' MINUTE, 'yyyy-MM-dd HH:mm:ss') 
    AND ToDateTime(now(), 'yyyy-MM-dd HH:mm:ss') 
GROUP BY 
    days
