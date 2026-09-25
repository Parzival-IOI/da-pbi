select st.StoreID, st.Store, count(st.Store), sum(s.Amount ), st.Latitude, st.Longitude, st.Type from sales_dated s
	left JOIN product p on s.ProductID  = p.ProductID
	left join store st on st.StoreID = s.StoreID 
where s.Status = 'Sold'
	and (:month = '' or s.year_month = :month)
	and (:dim = '' or (:dim = 'Product' and p.Product = :item) or (:dim = 'Category' and p.Category = :item))
group by st.Store, st.StoreID, st.Latitude, st.Longitude, st.Type
order by sum(s.Amount ) desc
