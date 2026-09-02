import { Metadata } from "next";
import { UserManagementView } from "@/components/users/UserManagementView";

export const metadata: Metadata = {
  title: "Quản lý Người dùng & Ma trận Duyệt | PO Preflight",
  description: "Quản lý danh sách người dùng, vai trò RBAC và thiết lập ma trận phê duyệt phân tầng",
};

export default function UsersPage() {
  return <UserManagementView />;
}
