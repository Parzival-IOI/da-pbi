select ap.Product, count(ap.Product), sum(s.Amount ), sum(s.Unit ) from sales_dated s
	left JOIN product p on s.ProductID  = p.ProductID
	left join associated_product ap on p.ProductID = ap.ProductID
where s.Status = 'Sold'
	and (:store_id = 0 or s.StoreID = :store_id)
	and (:month = '' or s.year_month = :month)
group by ap.Product
order by sum(s.Amount ) desc
