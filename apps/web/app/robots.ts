import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://popreflight.vn";

  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/landing"],
        disallow: ["/api/", "/_sites-preview/"],
      },
      {
        userAgent: "Googlebot",
        allow: ["/", "/landing", "/orders", "/staging", "/rag-playground", "/audit-certificate", "/settings"],
        disallow: ["/api/"],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
