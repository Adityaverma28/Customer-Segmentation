import React, { useState } from 'react';
import { ScatterChart, Scatter, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Upload, Users, Target, TrendingUp, AlertCircle } from 'lucide-react';
import Papa from 'papaparse';
import _ from 'lodash';

const CustomerSegmentationTool = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState('');
  const [selectedSegment, setSelectedSegment] = useState('all');

  const SEGMENT_COLORS = {
    'Champions': '#10b981',
    'Loyal Customers': '#3b82f6',
    'Potential Loyalists': '#8b5cf6',
    'At Risk': '#f59e0b',
    'Need Attention': '#ef4444',
    'Lost': '#64748b'
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFileName(file.name);
      setLoading(true);
      
      Papa.parse(file, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: (results) => {
          processCustomerData(results.data);
          setLoading(false);
        },
        error: () => {
          alert('Error parsing CSV file');
          setLoading(false);
        }
      });
    }
  };

  const calculateRFMScores = (customerData) => {
    const today = new Date();
    
    return customerData.map(customer => {
      const lastPurchaseDate = new Date(customer.lastPurchase);
      const recency = Math.floor((today - lastPurchaseDate) / (1000 * 60 * 60 * 24));
      
      return {
        customerId: customer.customerId,
        recency,
        frequency: customer.frequency,
        monetary: customer.monetary
      };
    });
  };

  const assignRFMScore = (value, sorted, isRecency = false) => {
    const quintile = Math.ceil((sorted.indexOf(value) + 1) / sorted.length * 5);
    return isRecency ? (6 - quintile) : quintile;
  };

  const segmentCustomer = (r, f, m) => {
    const rfmScore = r + f + m;
    
    if (r >= 4 && f >= 4 && m >= 4) return 'Champions';
    if (r >= 3 && f >= 3 && m >= 3) return 'Loyal Customers';
    if (r >= 3 && f <= 3 && m >= 2) return 'Potential Loyalists';
    if (r <= 2 && f >= 3 && m >= 3) return 'At Risk';
    if (r <= 3 && f <= 2 && m <= 3) return 'Need Attention';
    return 'Lost';
  };

  const processCustomerData = (rawData) => {
    const customerGroups = _.groupBy(rawData, row => row.CustomerID || row.Customer);
    
    const customerMetrics = Object.entries(customerGroups).map(([customerId, transactions]) => {
      const dates = transactions
        .map(t => new Date(t.Date || t.PurchaseDate))
        .filter(d => !isNaN(d));
      
      const lastPurchase = dates.length > 0 ? new Date(Math.max(...dates)) : new Date();
      const frequency = transactions.length;
      const monetary = _.sumBy(transactions, t => t.Revenue || t.Amount || 0);
      
      return {
        customerId,
        lastPurchase: lastPurchase.toISOString(),
        frequency,
        monetary: Math.round(monetary)
      };
    });

    const rfmData = calculateRFMScores(customerMetrics);
    
    const sortedRecency = _.sortBy(rfmData.map(c => c.recency));
    const sortedFrequency = _.sortBy(rfmData.map(c => c.frequency));
    const sortedMonetary = _.sortBy(rfmData.map(c => c.monetary));

    const segmentedCustomers = rfmData.map(customer => {
      const rScore = assignRFMScore(customer.recency, sortedRecency, true);
      const fScore = assignRFMScore(customer.frequency, sortedFrequency);
      const mScore = assignRFMScore(customer.monetary, sortedMonetary);
      const segment = segmentCustomer(rScore, fScore, mScore);
      
      return {
        ...customer,
        rScore,
        fScore,
        mScore,
        segment
      };
    });

    const segmentStats = _.chain(segmentedCustomers)
      .groupBy('segment')
      .map((customers, segment) => ({
        segment,
        count: customers.length,
        avgMonetary: Math.round(_.meanBy(customers, 'monetary')),
        totalRevenue: Math.round(_.sumBy(customers, 'monetary')),
        color: SEGMENT_COLORS[segment]
      }))
      .orderBy('totalRevenue', 'desc')
      .value();

    const avgMetrics = {
      recency: Math.round(_.meanBy(segmentedCustomers, 'recency')),
      frequency: Math.round(_.meanBy(segmentedCustomers, 'frequency') * 10) / 10,
      monetary: Math.round(_.meanBy(segmentedCustomers, 'monetary'))
    };

    setData({
      customers: segmentedCustomers,
      segmentStats,
      avgMetrics,
      totalCustomers: segmentedCustomers.length
    });
  };

  const generateSampleData = () => {
    const customers = ['C001', 'C002', 'C003', 'C004', 'C005', 'C006', 'C007', 'C008'];
    const sampleData = [];
    
    customers.forEach(customer => {
      const numTransactions = Math.floor(Math.random() * 8) + 1;
      for (let i = 0; i < numTransactions; i++) {
        const daysAgo = Math.floor(Math.random() * 365);
        const date = new Date();
        date.setDate(date.getDate() - daysAgo);
        
        sampleData.push({
          CustomerID: customer,
          Date: date.toISOString().split('T')[0],
          Revenue: Math.floor(Math.random() * 500) + 50
        });
      }
    });
    
    processCustomerData(sampleData);
    setFileName('sample-customer-data.csv');
  };

  const filteredCustomers = data?.customers.filter(c => 
    selectedSegment === 'all' || c.segment === selectedSegment
  ) || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-2">Customer Segmentation & RFM Analysis</h1>
          <p className="text-slate-600">Analyze customer behavior using Recency, Frequency, and Monetary metrics</p>
        </div>

        {!data ? (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <Users className="w-16 h-16 mx-auto mb-4 text-indigo-500" />
            <h2 className="text-2xl font-semibold mb-4 text-slate-800">Start Your Analysis</h2>
            <p className="text-slate-600 mb-6">Upload a CSV with columns: CustomerID, Date, Revenue</p>
            
            <div className="flex gap-4 justify-center">
              <label className="cursor-pointer bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition">
                {loading ? 'Processing...' : 'Upload CSV File'}
                <input 
                  type="file" 
                  accept=".csv" 
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={loading}
                />
              </label>
              
              <button
                onClick={generateSampleData}
                className="bg-slate-600 text-white px-6 py-3 rounded-lg hover:bg-slate-700 transition"
              >
                Use Sample Data
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-4 flex justify-between items-center">
              <span className="text-slate-700">Analyzing: <strong>{fileName}</strong></span>
              <label className="cursor-pointer bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 transition text-sm">
                Upload Different File
                <input 
                  type="file" 
                  accept=".csv" 
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>

            {/* Overview Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-2">
                  <Users className="w-8 h-8 text-indigo-500" />
                  <span className="text-sm text-slate-500">Total</span>
                </div>
                <p className="text-3xl font-bold text-slate-800">{data.totalCustomers}</p>
                <p className="text-slate-600 text-sm mt-1">Customers</p>
              </div>

              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-2">
                  <TrendingUp className="w-8 h-8 text-green-500" />
                  <span className="text-sm text-slate-500">Avg</span>
                </div>
                <p className="text-3xl font-bold text-slate-800">{data.avgMetrics.recency}</p>
                <p className="text-slate-600 text-sm mt-1">Days Since Purchase</p>
              </div>

              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-2">
                  <Target className="w-8 h-8 text-blue-500" />
                  <span className="text-sm text-slate-500">Avg</span>
                </div>
                <p className="text-3xl font-bold text-slate-800">{data.avgMetrics.frequency}</p>
                <p className="text-slate-600 text-sm mt-1">Purchases per Customer</p>
              </div>

              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-2">
                  <AlertCircle className="w-8 h-8 text-purple-500" />
                  <span className="text-sm text-slate-500">Avg</span>
                </div>
                <p className="text-3xl font-bold text-slate-800">${data.avgMetrics.monetary}</p>
                <p className="text-slate-600 text-sm mt-1">Customer Value</p>
              </div>
            </div>

            {/* Segment Distribution */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold mb-4 text-slate-800">Customer Segments</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.segmentStats}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="segment" angle={-15} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => {
                      if (name === 'count') return [value, 'Customers'];
                      if (name === 'totalRevenue') return [`$${value.toLocaleString()}`, 'Total Revenue'];
                      return value;
                    }}
                  />
                  <Legend />
                  <Bar dataKey="count" name="Customers">
                    {data.segmentStats.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* RFM Scatter Plot */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold text-slate-800">Customer Distribution (Frequency vs Monetary)</h3>
                <select
                  value={selectedSegment}
                  onChange={(e) => setSelectedSegment(e.target.value)}
                  className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="all">All Segments</option>
                  {data.segmentStats.map(s => (
                    <option key={s.segment} value={s.segment}>{s.segment}</option>
                  ))}
                </select>
              </div>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="frequency" name="Frequency" label={{ value: 'Purchase Frequency', position: 'bottom' }} />
                  <YAxis dataKey="monetary" name="Monetary" label={{ value: 'Total Spend ($)', angle: -90, position: 'left' }} />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }}
                    formatter={(value, name) => {
                      if (name === 'Monetary') return `$${value}`;
                      return value;
                    }}
                  />
                  <Legend />
                  <Scatter 
                    name="Customers" 
                    data={filteredCustomers} 
                    fill="#8884d8"
                  >
                    {filteredCustomers.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={SEGMENT_COLORS[entry.segment]} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            {/* Segment Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {data.segmentStats.map(segment => (
                <div key={segment.segment} className="bg-white rounded-lg shadow-lg p-6 border-l-4" style={{ borderColor: segment.color }}>
                  <h4 className="text-lg font-semibold mb-3" style={{ color: segment.color }}>
                    {segment.segment}
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Customers:</span>
                      <span className="font-semibold text-slate-800">{segment.count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Avg Value:</span>
                      <span className="font-semibold text-slate-800">${segment.avgMonetary.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Total Revenue:</span>
                      <span className="font-semibold text-slate-800">${segment.totalRevenue.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomerSegmentationTool;
