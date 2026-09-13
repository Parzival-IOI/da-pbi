select sum(s.Amount ) from sales s
	left JOIN product p on s.ProductID  = p.ProductID
where s.Status = 'Returned'