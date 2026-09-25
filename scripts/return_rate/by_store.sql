select st.Store, st.Latitude, st.Longitude, st.Type,
	sum(case when s.Status = 'Sold' then s.Amount else 0 end) as sold,
	sum(case when s.Status = 'Returned' then s.Amount else 0 end) as returned
from sales s
	left join product p on s.ProductID = p.ProductID
	left join store st on st.StoreID = s.StoreID
where (:dim = 'Product' and p.Product = :item) or (:dim = 'Category' and p.Category = :item)
group by st.Store, st.Latitude, st.Longitude, st.Type
order by st.Store
