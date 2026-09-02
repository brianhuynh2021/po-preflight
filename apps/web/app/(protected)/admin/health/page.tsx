import { AdminHealthView } from "@/components/admin/AdminHealthView";

export const metadata = {
  title: "Giám sát & Sức khỏe Hệ thống | PO Preflight",
  description: "Trang tổng quan giám sát hạ tầng, độ trễ cơ sở dữ liệu, hàng đợi ERP outbox và truy vết lỗi 5xx.",
};

export default function AdminHealthPage() {
  return <AdminHealthView />;
}
