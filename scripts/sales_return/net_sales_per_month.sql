with cte as (
   select *,
       SUBSTR(s.Date, -4) || '-' ||
       CASE SUBSTR(
           s.Date,
           INSTR(s.Date, ', ') + 2,
           INSTR(SUBSTR(s.Date, INSTR(s.Date, ', ') + 2), ' ') - 1
       )
           WHEN 'January'   THEN '01' WHEN 'February' THEN '02' WHEN 'March'     THEN '03'
           WHEN 'April'     THEN '04' WHEN 'May'      THEN '05' WHEN 'June'      THEN '06'
           WHEN 'July'      THEN '07' WHEN 'August'   THEN '08' WHEN 'September' THEN '09'
           WHEN 'October'   THEN '10' WHEN 'November' THEN '11' WHEN 'December'  THEN '12'
       END || '-' ||
       PRINTF('%02d', CAST(
           SUBSTR(
               s.Date,
               INSTR(s.Date, ', ') + 2 + INSTR(SUBSTR(s.Date, INSTR(s.Date, ', ') + 2), ' '),
               2
           ) AS INTEGER
       )) as formated_date
   from sales s
)
select 
   STRFTIME('%Y-%m', s.formated_date) as year_month,
   sum(s.amount) as total_price 
from cte s
   left JOIN product p on s.ProductID = p.ProductID 
where s.status = 'Sold'
group by year_month
order by year_month