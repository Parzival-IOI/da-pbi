select p.Category , count(p.Category ), sum(s.Amount ) from sales s
	left JOIN product p on s.ProductID  = p.ProductID
where s.Status = 'Sold'
group by p.Category 
order by sum(s.Amount ) desc