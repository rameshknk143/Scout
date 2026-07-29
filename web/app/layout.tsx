import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ScoutVeda",
  description: "Find products worth sourcing — KNK Enterprises",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <body className="min-h-full bg-bg text-text" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
