import { MobileOrderApprovalView } from "@/components/orders/MobileOrderApprovalView";

export default async function MobileOrderPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <MobileOrderApprovalView orderId={id} />;
}
