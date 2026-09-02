import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://popreflight.vn";

  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/pricing", "/security", "/landing"],
        disallow: [
          "/api/",
          "/overview",
          "/orders",
          "/catalog",
          "/rules",
          "/settings",
          "/audit-log",
          "/erp-sync",
          "/agent-graph",
          "/rag-playground",
          "/audit-certificate",
          "/staging",
          "/login",
        ],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
