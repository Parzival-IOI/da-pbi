select st.StoreID, st.Store, count(st.Store), sum(s.Amount ) from sales s
	left JOIN product p on s.ProductID  = p.ProductID
	left join store st on st.StoreID = s.StoreID 
where s.Status = 'Sold'
group by st.Store, st.StoreID 
order by sum(s.Amount ) desc