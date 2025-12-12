import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Therapy LLM | AI for Therapeutic Conversations",
  description: "A fine-tuned AI trained on real therapist conversations. Empathetic, supportive responses for mental health research.",
  openGraph: {
    title: "Therapy LLM",
    description: "A fine-tuned AI for therapeutic conversations",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

