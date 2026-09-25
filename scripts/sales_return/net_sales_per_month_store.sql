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
   st.Store as store,
   sum(s.amount) as total_price
from cte s
   left join store st on st.StoreID = s.StoreID
   left join product p on s.ProductID = p.ProductID
where s.status = 'Returned'
	and (:store_id = 0 or s.StoreID = :store_id)
	and (:dim = '' or (:dim = 'Product' and p.Product = :item) or (:dim = 'Category' and p.Category = :item))
group by year_month, st.Store
order by year_month, st.Store
