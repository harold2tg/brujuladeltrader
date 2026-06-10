import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "La Brújula del Trader",
  description: "Plataforma de análisis estadístico para traders de XAUUSD",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return children;
}
