import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Zomato AI — Restaurant Recommendations",
  description:
    "AI-powered restaurant recommendations for Bangalore. Enter your preferences and get personalized picks ranked by Groq LLM.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
