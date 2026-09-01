import { LandingPageView } from "@/components/landing/LandingPageView";

export const metadata = {
  title: "PO Preflight — Autonomous B2B Order Intake & Preflight Gatekeeper",
  description: "Stop pricing leaks, out-of-stock orders, and manual data entry. Ingest, validate against warehouse catalog in <15ms, and sync directly to SAP/Odoo.",
};

export default function LandingPage() {
  return <LandingPageView />;
}
