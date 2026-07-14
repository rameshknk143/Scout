import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ram's Scout",
  description: "Personal product-intelligence radar — KNK Enterprises",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full bg-bg text-text">
        {children}
      </body>
    </html>
  );
}
