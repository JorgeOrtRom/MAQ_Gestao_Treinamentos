import './globals.css';
import React from 'react';

export const metadata = {
  title: 'MAQ Gestão - Sistema de Treinamentos',
  description: 'Plataforma Enterprise de Gestão de Treinamentos',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt">
      <body className="bg-slate-100 font-sans antialiased">{children}</body>
    </html>
  );
}