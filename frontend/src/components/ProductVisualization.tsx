import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface Product {
  product_code: string;
  cost_before_tax: number;
}

interface ProductVisualizationProps {
  data: Product[];
}

const ProductVisualization = ({ data }: ProductVisualizationProps) => {
  const chartRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!data || data.length === 0 || !chartRef.current) return;

    // Clear any existing chart
    d3.select(chartRef.current).selectAll('*').remove();

    // Set dimensions
    const width = 600;
    const height = 400;
    const margin = { top: 30, right: 30, bottom: 70, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create SVG
    const svg = d3.select(chartRef.current)
      .attr('width', width)
      .attr('height', height);

    // Create chart group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create scales
    const x = d3.scaleBand()
      .domain(data.map(d => d.product_code))
      .range([0, innerWidth])
      .padding(0.2);

    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.cost_before_tax) || 0])
      .nice()
      .range([innerHeight, 0]);

    // Add X axis
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em');

    // Add Y axis
    g.append('g')
      .call(d3.axisLeft(y));

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', margin.top / 2)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .text(`Product Costs (${data.length} Products)`);

    // Add bars
    g.selectAll('.bar')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.product_code) || 0)
      .attr('y', d => y(d.cost_before_tax))
      .attr('width', x.bandwidth())
      .attr('height', d => innerHeight - y(d.cost_before_tax))
      .attr('fill', 'steelblue')
      .on('mouseover', function(event, d) {
        d3.select(this).attr('fill', '#ff9900');
        
        // Show tooltip
        tooltip
          .style('opacity', 1)
          .html(`<strong>${d.product_code}</strong><br>Cost: $${d.cost_before_tax.toFixed(2)}`)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', function() {
        d3.select(this).attr('fill', 'steelblue');
        tooltip.style('opacity', 0);
      });

    // Add tooltip
    const tooltip = d3.select('body').append('div')
      .attr('class', 'tooltip')
      .style('opacity', 0);

  }, [data]);

  return (
    <div className="visualization-container">
      <svg ref={chartRef}></svg>
    </div>
  );
};

export default ProductVisualization;