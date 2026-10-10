import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "La Brújula del Trader",
  description: "Plataforma de análisis estadístico para traders de XAUUSD",
};

/**
 * Root layout only forwards metadata and global styles.
 * The `<html>` / `<body>` shell lives in app/[locale]/layout.tsx so the
 * document is rendered once, with the correct `lang` attribute.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return children;
}
