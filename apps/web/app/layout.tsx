import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const viewport: Viewport = {
  themeColor: "#090d16",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || "https://popreflight.vn"),
  title: {
    default: "PO Preflight — Purchase Order Operations | Nhật Minh Technology",
    template: "%s | PO Preflight — Nhật Minh Technology",
  },
  description:
    "Cổng kiểm soát an toàn tự động cho đơn đặt hàng B2B dành cho doanh nghiệp phân phối & bán buôn. Tự kiểm tra tổng tiền dòng so với tổng đơn, đối soát giá và tồn kho, duyệt tức thì qua mobile bot Telegram & Zalo.",
  keywords: [
    "PO Preflight",
    "Kiểm soát đơn hàng B2B",
    "Bóc tách hóa đơn tự động",
    "Khớp mã kho SKU",
    "Phê duyệt Telegram Zalo",
    "Đồng bộ ERP MISA Bravo Fast Odoo",
    "Nhật Minh Technology",
    "Nhật ký bất biến SHA-256",
  ],
  authors: [{ name: "Nhật Minh Technology", url: "https://popreflight.vn" }],
  creator: "Công ty Nhật Minh Technology",
  publisher: "Nhật Minh Technology",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    title: "PO Preflight — Cổng Kiểm Soát Đơn Hàng B2B Tự Động Hóa",
    description:
      "Tự động hóa kiểm soát đơn đặt hàng B2B, bóc tách hóa đơn, đối soát giá và tồn kho, duyệt tức thì qua mobile bot Telegram & Zalo.",
    url: "https://popreflight.vn",
    siteName: "PO Preflight by Nhật Minh Technology",
    locale: "vi_VN",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "PO Preflight — Cổng Kiểm Soát Đơn Hàng B2B Tự Động Hóa",
    description:
      "Cổng kiểm soát an toàn tự động cho đơn đặt hàng B2B. Đối soát số học, 4-Tier RAG, phê duyệt 1 chạm Telegram/Zalo và đồng bộ ERP.",
    creator: "@nhatminhtech",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: "https://popreflight.vn",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://popreflight.vn/#organization",
      name: "Công ty Nhật Minh Technology",
      url: "https://popreflight.vn",
      logo: "https://popreflight.vn/logo.png",
      contactPoint: {
        "@type": "ContactPoint",
        telephone: "+84-28-7300-6868",
        contactType: "Customer Support",
        email: "contact@popreflight.vn",
        areaServed: "VN",
        availableLanguage: ["Vietnamese", "English"],
      },
    },
    {
      "@type": "SoftwareApplication",
      "@id": "https://popreflight.vn/#software",
      name: "PO Preflight",
      applicationCategory: "BusinessApplication",
      operatingSystem: "Cloud, Web, Mobile (Telegram/Zalo Bot)",
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "VND",
        description: "14-day free pilot trial for enterprise distributors",
      },
      publisher: {
        "@id": "https://popreflight.vn/#organization",
      },
      description:
        "Hệ thống kiểm soát và tự động hóa tiền kiểm đơn đặt hàng B2B, phát hiện sai sót số học, tồn kho và chênh lệch giá trước khi chuyển vào ERP.",
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("theme");if(t!=="light"&&t!=="dark"){t="dark";}if(t==="dark"){document.documentElement.classList.add("dark");}}catch(e){}})();`,
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
