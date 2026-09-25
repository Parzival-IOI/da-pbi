-- :dim is 'Product' or 'Category'; :item is the selected name
select p.Product, p.Category, p."Product Image" as board_image, ap."Product Image" as icon_image, p."Category Image" as category_image
from product p
	left join associated_product ap on ap.ProductID = p.ProductID
where (:dim = 'Product' and p.Product = :item) or (:dim = 'Category' and p.Category = :item)
order by p.ProductID
