import { SecurityView } from "@/components/security/SecurityView";

export const metadata = {
  title: "An Ninh Dữ Liệu & Tuân Thủ Pháp Lý — PO Preflight",
  description: "Chính sách an ninh dữ liệu, mã hóa AES-256/TLS 1.3, chuỗi băm Merkle SHA-256 và tuân thủ Nghị định 13/2023/NĐ-CP của PO Preflight.",
};

export default function SecurityPage() {
  return <SecurityView />;
}
