import React from 'react';

interface Product {
  product_code: string;
  cost_before_tax: number;
}

interface ProductListProps {
  products: Product[];
}

const ProductList: React.FC<ProductListProps> = ({ products }) => {
  if (!products || products.length === 0) {
    return (
      <div>
        <p>No products found in API response.</p>
        <p>Please try a different query or check if data exists in the database.</p>
      </div>
    );
  }

  return (
    <div className="product-list">
      <h3>Product List from API ({products.length} products)</h3>
      <table>
        <thead>
          <tr>
            <th>Product Code</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product, index) => (
            <tr key={index}>
              <td>{product.product_code}</td>
              <td>${product.cost_before_tax.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ProductList;