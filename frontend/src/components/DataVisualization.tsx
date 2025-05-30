import { useState } from 'react';
import ProductVisualization from './ProductVisualization';
import ProductList from './ProductList';
import './visualization.css';

interface Product {
  product_code: string;
  cost_before_tax: number;
}

interface DataVisualizationProps {
  data: any[];
}

const DataVisualization = ({ data }: DataVisualizationProps) => {
  const [activeTab, setActiveTab] = useState<'chart' | 'list'>('chart');
  
  // Process data for visualization
  console.log('Data received in DataVisualization:', data);
  
  const products = data
    .filter(item => item !== null && typeof item === 'object')
    .map(item => ({
      product_code: item.product_code || 'Unknown',
      cost_before_tax: typeof item.cost_before_tax === 'number' 
        ? item.cost_before_tax 
        : parseFloat(item.cost_before_tax) || 0
    }));

  if (!products.length) {
    return (
      <div className="visualization-container">
        <p>No product data available for visualization.</p>
        <p>Try using a different Payer Account ID or Invoice ID.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="visualization-tabs">
        <div 
          className={`visualization-tab ${activeTab === 'chart' ? 'active' : ''}`}
          onClick={() => setActiveTab('chart')}
        >
          Chart View
        </div>
        <div 
          className={`visualization-tab ${activeTab === 'list' ? 'active' : ''}`}
          onClick={() => setActiveTab('list')}
        >
          List View
        </div>
      </div>
      
      {activeTab === 'chart' ? (
        <ProductVisualization data={products} />
      ) : (
        <ProductList products={products} />
      )}
    </div>
  );
};

export default DataVisualization;