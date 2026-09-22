import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts';
import { PieChart as PieIcon, BarChart3 } from 'lucide-react';

const COLORS = ['#6366f1', '#a855f7', '#ec4899', '#10b981', '#f59e0b', '#3b82f6', '#64748b'];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="bg-slate-900/95 border border-slate-700/80 p-3 rounded-2xl shadow-2xl backdrop-blur-md">
        <p className="text-xs font-bold text-slate-300 mb-0.5">{data.name || label}</p>
        <p className="text-xs font-bold text-slate-100 flex items-center space-x-1">
          <span className="text-cyan-400">Monthly Spend :</span>
          <span className="text-emerald-400 font-black text-sm">₹{parseFloat(data.value).toFixed(2)}</span>
        </p>
      </div>
    );
  }
  return null;
};

export default function SpendAnalytics({ subscriptions }) {
  // Aggregate spending by category
  const categoryDataMap = subscriptions.reduce((acc, sub) => {
    if (sub.status === 'cancelled') return acc;
    const cat = sub.category || 'General';
    let monthlyAmount = parseFloat(sub.amount) || 0;
    if (sub.billing_cycle === 'yearly') monthlyAmount = monthlyAmount / 12;
    if (sub.billing_cycle === 'weekly') monthlyAmount = monthlyAmount * 4;

    acc[cat] = (acc[cat] || 0) + monthlyAmount;
    return acc;
  }, {});

  const categoryChartData = Object.keys(categoryDataMap).map(cat => ({
    name: cat,
    value: parseFloat(categoryDataMap[cat].toFixed(2))
  })).sort((a, b) => b.value - a.value);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      
      {/* Category Spend Distribution Pie Chart */}
      <div className="glass-panel rounded-3xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <PieIcon className="w-5 h-5 text-indigo-400" />
            <span>Category Spending Breakdown</span>
          </h3>
          <span className="text-xs text-slate-400">Monthly normalized</span>
        </div>

        <div className="h-64 w-full">
          {categoryChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {categoryChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">No active data to plot</div>
          )}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-center gap-3 mt-2 text-xs">
          {categoryChartData.map((item, idx) => (
            <div key={item.name} className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></span>
              <span className="text-slate-300 font-medium">{item.name}</span>
              <span className="text-slate-500">(₹{item.value.toFixed(0)})</span>
            </div>
          ))}
        </div>
      </div>

      {/* Monthly vs Yearly Bar Breakdown */}
      <div className="glass-panel rounded-3xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-purple-400" />
            <span>Top Subscriptions by Cost</span>
          </h3>
          <span className="text-xs text-slate-400">Highest debits</span>
        </div>

        <div className="h-64 w-full">
          {subscriptions.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={subscriptions.slice(0, 5).map(s => ({ name: s.name, amount: parseFloat(s.amount) }))}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="amount" fill="#6366f1" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">No active data to plot</div>
          )}
        </div>
        <div className="mt-2 text-xs text-center text-slate-400">
          Showing top recurring costs sorted by billing amount
        </div>
      </div>

    </div>
  );
}
