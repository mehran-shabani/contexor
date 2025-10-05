'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import Card from '@/components/ui/Card';
import Spinner from '@/components/ui/Spinner';
import SimpleChart from '@/components/SimpleChart';
import { usageApi } from '@/lib/api';

interface UsageSummary {
  scope: string;
  period: string;
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  limit?: {
    requests_limit: number;
    tokens_limit: number;
    cost_limit: number;
    usage_percentage: {
      requests: number;
      tokens: number;
      cost: number;
    };
  };
  breakdown_by_model?: Record<string, {
    requests: number;
    tokens: number;
    cost: number;
  }>;
  daily_usage?: Array<{
    date: string;
    requests: number;
    tokens: number;
    cost: number;
  }>;
}

export default function UsagePage() {
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState<'requests' | 'tokens' | 'cost'>('requests');
  const [selectedMonth, setSelectedMonth] = useState(
    new Date().toISOString().slice(0, 7) // YYYY-MM format
  );

  useEffect(() => {
    loadUsage();
  }, [selectedMonth]);

  const loadUsage = async () => {
    setLoading(true);
    try {
      const response = await usageApi.getSummary({
        scope: 'user',
        month: selectedMonth,
      });

      if (response.data.success) {
        setSummary(response.data.data || null);
      }
    } catch (error) {
      console.error('Error loading usage:', error);
    } finally {
      setLoading(false);
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getProgressTextColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-700';
    if (percentage >= 70) return 'text-yellow-700';
    return 'text-green-700';
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">گزارش مصرف</h1>
            <p className="text-gray-600 mt-1">آمار استفاده از API</p>
          </div>

          {/* Month Selector */}
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {!summary ? (
          <Card className="text-center py-12">
            <p className="text-gray-600">داده‌ای برای نمایش وجود ندارد</p>
          </Card>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <h3 className="text-sm text-gray-600 mb-2">تعداد درخواست‌ها</h3>
                <p className="text-3xl font-bold text-gray-900 mb-1">
                  {summary.total_requests.toLocaleString()}
                </p>
                {summary.limit && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>از {summary.limit.requests_limit.toLocaleString()}</span>
                      <span
                        className={getProgressTextColor(
                          summary.limit.usage_percentage.requests
                        )}
                      >
                        {summary.limit.usage_percentage.requests.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getProgressColor(
                          summary.limit.usage_percentage.requests
                        )}`}
                        style={{
                          width: `${Math.min(
                            summary.limit.usage_percentage.requests,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </Card>

              <Card>
                <h3 className="text-sm text-gray-600 mb-2">تعداد توکن‌ها</h3>
                <p className="text-3xl font-bold text-gray-900 mb-1">
                  {summary.total_tokens.toLocaleString()}
                </p>
                {summary.limit && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>از {summary.limit.tokens_limit.toLocaleString()}</span>
                      <span
                        className={getProgressTextColor(
                          summary.limit.usage_percentage.tokens
                        )}
                      >
                        {summary.limit.usage_percentage.tokens.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getProgressColor(
                          summary.limit.usage_percentage.tokens
                        )}`}
                        style={{
                          width: `${Math.min(
                            summary.limit.usage_percentage.tokens,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </Card>

              <Card>
                <h3 className="text-sm text-gray-600 mb-2">هزینه کل</h3>
                <p className="text-3xl font-bold text-gray-900 mb-1">
                  ${summary.total_cost.toFixed(2)}
                </p>
                {summary.limit && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>از ${summary.limit.cost_limit.toFixed(2)}</span>
                      <span
                        className={getProgressTextColor(
                          summary.limit.usage_percentage.cost
                        )}
                      >
                        {summary.limit.usage_percentage.cost.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getProgressColor(
                          summary.limit.usage_percentage.cost
                        )}`}
                        style={{
                          width: `${Math.min(
                            summary.limit.usage_percentage.cost,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </Card>
            </div>

            {/* Daily Usage Chart */}
            {summary.daily_usage && summary.daily_usage.length > 0 && (
              <Card>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-lg font-semibold">مصرف روزانه</h2>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSelectedMetric('requests')}
                      className={`px-3 py-1 text-sm rounded ${
                        selectedMetric === 'requests'
                          ? 'bg-primary-100 text-primary-700 font-medium'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      درخواست‌ها
                    </button>
                    <button
                      onClick={() => setSelectedMetric('tokens')}
                      className={`px-3 py-1 text-sm rounded ${
                        selectedMetric === 'tokens'
                          ? 'bg-primary-100 text-primary-700 font-medium'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      توکن‌ها
                    </button>
                    <button
                      onClick={() => setSelectedMetric('cost')}
                      className={`px-3 py-1 text-sm rounded ${
                        selectedMetric === 'cost'
                          ? 'bg-primary-100 text-primary-700 font-medium'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      هزینه
                    </button>
                  </div>
                </div>
                <SimpleChart data={summary.daily_usage} metric={selectedMetric} />
              </Card>
            )}

            {/* Model Breakdown */}
            {summary.breakdown_by_model &&
              Object.keys(summary.breakdown_by_model).length > 0 && (
                <Card>
                  <h2 className="text-lg font-semibold mb-4">تفکیک بر اساس مدل</h2>
                  <div className="space-y-4">
                    {Object.entries(summary.breakdown_by_model).map(
                      ([model, data]) => (
                        <div key={model} className="border-b pb-4 last:border-b-0">
                          <div className="flex justify-between items-center mb-2">
                            <h3 className="font-medium text-gray-900">{model}</h3>
                            <span className="text-sm text-gray-600">
                              {data.requests} درخواست
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-gray-600">توکن‌ها:</span>
                              <span className="mr-2 font-medium">
                                {data.tokens.toLocaleString()}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-600">هزینه:</span>
                              <span className="mr-2 font-medium">
                                ${data.cost.toFixed(2)}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-600">میانگین:</span>
                              <span className="mr-2 font-medium">
                                ${(data.cost / data.requests).toFixed(3)}
                              </span>
                            </div>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </Card>
              )}
          </>
        )}
      </div>
    </Layout>
  );
}
