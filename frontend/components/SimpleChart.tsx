'use client';

interface DataPoint {
  date: string;
  requests: number;
  tokens: number;
  cost: number;
}

interface SimpleChartProps {
  data: DataPoint[];
  metric: 'requests' | 'tokens' | 'cost';
}

export default function SimpleChart({ data, metric }: SimpleChartProps) {
  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        داده‌ای برای نمایش وجود ندارد
      </div>
    );
  }

  const values = data.map((d) => d[metric]);
  const maxValue = Math.max(...values);
  const minValue = Math.min(...values);
  const range = maxValue - minValue || 1;

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-2 h-64">
        {data.map((point, index) => {
          const height = ((point[metric] - minValue) / range) * 100;
          const isHighest = point[metric] === maxValue;

          return (
            <div key={index} className="flex-1 flex flex-col items-center gap-2">
              <div className="relative w-full flex-1 flex items-end">
                <div className="relative w-full group">
                  <div
                    className={`w-full rounded-t transition-all ${
                      isHighest
                        ? 'bg-primary-600'
                        : 'bg-primary-400 hover:bg-primary-500'
                    }`}
                    style={{ height: `${Math.max(height, 5)}%` }}
                  />
                  
                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                    <div className="font-bold mb-1">
                      {new Date(point.date).toLocaleDateString('fa-IR', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </div>
                    <div>درخواست‌ها: {point.requests}</div>
                    <div>توکن‌ها: {point.tokens.toLocaleString()}</div>
                    <div>هزینه: ${point.cost.toFixed(2)}</div>
                  </div>
                </div>
              </div>

              <div className="text-xs text-gray-600 text-center">
                {new Date(point.date).toLocaleDateString('fa-IR', {
                  month: 'numeric',
                  day: 'numeric',
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-primary-400 rounded" />
          <span>روزانه</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-primary-600 rounded" />
          <span>بیشترین</span>
        </div>
      </div>
    </div>
  );
}
