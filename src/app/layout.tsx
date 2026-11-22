import type { Metadata } from "next";
import type { ReactNode } from "react";
import "@fontsource-variable/inter";
import "@fontsource-variable/manrope";
import "@fontsource/noto-sans-arabic/arabic-500.css";
import "katex/dist/katex.min.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "DecisionLab · Decision Theory & Analysis",
  description: "An interactive academic laboratory for decision analysis, decision trees, and Bayesian reasoning.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
