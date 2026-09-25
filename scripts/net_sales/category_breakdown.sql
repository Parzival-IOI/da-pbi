select p.Category , count(p.Category ), sum(s.Amount ), sum(s.Unit ) from sales_dated s
	left JOIN product p on s.ProductID  = p.ProductID
where s.Status = 'Sold'
	and (:store_id = 0 or s.StoreID = :store_id)
	and (:month = '' or s.year_month = :month)
group by p.Category 
order by sum(s.Amount ) desc