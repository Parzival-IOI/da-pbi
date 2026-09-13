select ap.Product, count(ap.Product), sum(s.Amount ) from sales s
	left JOIN product p on s.ProductID  = p.ProductID
	left join associated_product ap on p.ProductID = ap.ProductID
where s.Status = 'Returned'
group by ap.Product
order by sum(s.Amount ) desc
