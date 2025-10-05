'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Card from '@/components/ui/Card';
import { authApi } from '@/lib/api';
import { authStorage } from '@/lib/auth';

type Step = 'phone' | 'code';

export default function LoginPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>('phone');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [ttl, setTtl] = useState(120);

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Format phone number to +989xxxxxxxxx
      let formattedPhone = phoneNumber.trim();
      if (formattedPhone.startsWith('0')) {
        formattedPhone = '+98' + formattedPhone.slice(1);
      } else if (!formattedPhone.startsWith('+98')) {
        formattedPhone = '+98' + formattedPhone;
      }

      const response = await authApi.requestOtp(formattedPhone);

      if (response.data.success) {
        setPhoneNumber(formattedPhone);
        setTtl(response.data.data?.ttl || 120);
        setStep('code');
      } else {
        setError(response.data.error || 'خطا در ارسال کد تأیید');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'خطا در ارتباط با سرور');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authApi.verifyOtp(phoneNumber, code);

      if (response.data.success && response.data.data) {
        const { access, refresh, user } = response.data.data;
        
        // Save tokens and user data
        authStorage.setTokens({ access, refresh });
        authStorage.setUser(user);

        // Redirect to projects page
        router.push('/projects');
      } else {
        setError(response.data.error || 'کد تأیید نامعتبر است');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'خطا در تأیید کد');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setStep('phone');
    setCode('');
    setError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-primary-50 to-blue-100">
      <Card className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Contexor</h1>
          <p className="text-gray-600">
            {step === 'phone' ? 'ورود به سامانه' : 'تأیید شماره موبایل'}
          </p>
        </div>

        {step === 'phone' ? (
          <form onSubmit={handleRequestOtp} className="space-y-6">
            <Input
              label="شماره موبایل"
              type="tel"
              placeholder="09123456789"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              error={error}
              required
              dir="ltr"
              className="text-left"
            />

            <Button
              type="submit"
              className="w-full"
              isLoading={loading}
              disabled={!phoneNumber.trim()}
            >
              ارسال کد تأیید
            </Button>

            <p className="text-sm text-gray-600 text-center">
              با ورود به سامانه، شما{' '}
              <a href="#" className="text-primary-600 hover:underline">
                قوانین و مقررات
              </a>{' '}
              را می‌پذیرید.
            </p>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="space-y-6">
            <div>
              <p className="text-sm text-gray-600 mb-4">
                کد تأیید به شماره <span className="font-bold">{phoneNumber}</span> ارسال شد.
              </p>
              <Input
                label="کد تأیید"
                type="text"
                placeholder="123456"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                error={error}
                required
                maxLength={6}
                dir="ltr"
                className="text-center text-2xl tracking-widest"
              />
              <p className="text-xs text-gray-500 mt-2">
                کد تأیید تا {ttl} ثانیه معتبر است.
              </p>
            </div>

            <div className="space-y-3">
              <Button
                type="submit"
                className="w-full"
                isLoading={loading}
                disabled={code.length !== 6}
              >
                تأیید و ورود
              </Button>

              <Button
                type="button"
                variant="ghost"
                className="w-full"
                onClick={handleBack}
                disabled={loading}
              >
                بازگشت و تغییر شماره
              </Button>
            </div>

            <button
              type="button"
              className="text-sm text-primary-600 hover:underline w-full text-center"
              onClick={handleRequestOtp}
              disabled={loading}
            >
              ارسال مجدد کد
            </button>
          </form>
        )}
      </Card>
    </div>
  );
}
