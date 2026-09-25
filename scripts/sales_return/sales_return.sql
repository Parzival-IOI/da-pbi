select sum(s.Amount ) from sales_dated s
	left JOIN product p on s.ProductID  = p.ProductID
where s.Status = 'Returned'
	and (:store_id = 0 or s.StoreID = :store_id)
	and (:month = '' or s.year_month = :month)
	and (:dim = '' or (:dim = 'Product' and p.Product = :item) or (:dim = 'Category' and p.Category = :item))