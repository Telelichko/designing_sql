import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Companies Viewer',
  description: 'Просмотр компаний из базы данных',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className="bg-gray-50 text-gray-900 font-sans antialiased">
        {children}
      </body>
    </html>
  );
}