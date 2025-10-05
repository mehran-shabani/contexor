import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Contexor - مدیریت محتوای هوشمند',
  description: 'سامانه تولید و مدیریت محتوای هوشمند با AI',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fa" dir="rtl">
      <body className="antialiased min-h-screen bg-gray-50">{children}</body>
    </html>
  );
}
