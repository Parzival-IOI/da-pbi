with cte as (
   select s.Status, s.Amount,
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
       )) as sale_date
   from sales s
       left join product p on s.ProductID = p.ProductID
   where (:dim = 'Product' and p.Product = :item) or (:dim = 'Category' and p.Category = :item)
)
select sale_date,
	sum(case when Status = 'Sold' then Amount else 0 end) as sold,
	sum(case when Status = 'Returned' then Amount else 0 end) as returned
from cte
group by sale_date
order by sale_date
