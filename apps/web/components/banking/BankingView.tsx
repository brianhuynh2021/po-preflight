"use client";

import { useState, type FormEvent } from "react";
import { Download, FileCheck2, Landmark, Plus, Trash2 } from "lucide-react";
import { api, ApiError, describeError } from "@/app/lib/api/client";
import { money } from "@/app/lib/derive";
import { useMounted } from "@/app/lib/useMounted";
import type { BankingDocumentType, BankingInvoice, DisbursementAnalysis, DisbursementCase } from "@/app/lib/types";
import { StatusBadge } from "@/components/common/StatusBadge";
import styles from "./BankingView.module.css";

const documents: Array<[BankingDocumentType, string]> = [
  ["disbursement_request", "Đề nghị giải ngân"],
  ["credit_agreement", "Hợp đồng tín dụng"],
  ["purchase_contract", "Hợp đồng mua bán"],
  ["invoice", "Hóa đơn"],
];

const explanations: Record<string, [string, string]> = {
  DOCUMENTS_MISSING: ["Thiếu chứng từ bắt buộc", "Bổ sung các chứng từ còn thiếu và xác nhận lại checklist."],
  CONTRACT_EXPIRED: ["Hợp đồng tín dụng hết hiệu lực", "Kiểm tra hợp đồng hoặc văn bản gia hạn."],
  LIMIT_SNAPSHOT_STALE: ["Dữ liệu hạn mức chưa cập nhật trong ngày", "Lấy lại hạn mức và dư nợ từ nguồn được ngân hàng xác nhận."],
  LIMIT_SNAPSHOT_FUTURE: ["Ngày dữ liệu hạn mức nằm trong tương lai", "Kiểm tra ngày chốt dữ liệu hạn mức."],
  LIMIT_EXCEEDED: ["Số tiền đề nghị vượt hạn mức còn lại", "Đối chiếu hạn mức, dư nợ và số tiền đề nghị giải ngân."],
  INVOICES_MISSING: ["Chưa nhập hóa đơn", "Bổ sung dữ liệu hóa đơn làm căn cứ đối chiếu."],
  DUPLICATE_INVOICE: ["Hóa đơn trùng trong hồ sơ", "Kiểm tra số hóa đơn và mã số thuế bên bán; loại bỏ bản trùng."],
  BENEFICIARY_MISMATCH: ["Bên bán không khớp bên thụ hưởng", "Đối chiếu mã số thuế bên bán với bên thụ hưởng dự kiến."],
  BORROWER_MISMATCH: ["Bên mua không khớp khách hàng vay", "Đối chiếu mã số thuế bên mua với khách hàng vay."],
  INVOICE_FUTURE: ["Ngày hóa đơn nằm trong tương lai", "Kiểm tra ngày lập hóa đơn trên chứng từ gốc."],
  INVOICE_BALANCE_EXCEEDED: ["Số tiền đề nghị vượt giá trị hóa đơn còn lại", "Kiểm tra giá trị hóa đơn hợp lệ và phần đã được tài trợ."],
};

const emptyInvoice = (): BankingInvoice => ({ number: "", seller_tax_id: "", buyer_tax_id: "", amount: "", already_financed: "0", issued_on: "", source_reference: "" });
const emptyCase = (): DisbursementCase => ({
  case_id: "", borrower: "", borrower_tax_id: "", currency: "VND", requested_amount: "",
  beneficiary_tax_id: "", contract_reference: "", contract_valid_until: "",
  approved_limit: "", outstanding_amount: "0", limit_as_of: "", documents: [], invoices: [emptyInvoice()],
});

function todayInVietnam() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
}

export function BankingView() {
  const mounted = useMounted();
  const [draft, setDraft] = useState<DisbursementCase>(emptyCase);
  const [result, setResult] = useState<DisbursementAnalysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function update(next: DisbursementCase) {
    setDraft(next);
    setResult(null);
    setError("");
  }
  function sample() {
    const today = todayInVietnam();
    update({ case_id: "GN-DEMO-001", borrower: "Công ty Minh An (minh họa)", borrower_tax_id: "0101234567",
      currency: "VND", requested_amount: "850000000", beneficiary_tax_id: "0301234567",
      contract_reference: "HDTD-DEMO-001", contract_valid_until: "2099-12-31", approved_limit: "2000000000",
      outstanding_amount: "1200000000", limit_as_of: today, documents: documents.map(([key]) => key),
      invoices: [{ number: "HD-DEMO-001", seller_tax_id: "0301234567", buyer_tax_id: "0101234567",
        amount: "900000000", already_financed: "100000000", issued_on: today, source_reference: "Hóa đơn minh họa / trang 1" }],
    });
  }
  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError(""); setResult(null);
    try {
      setResult(await api.banking.analyze(draft));
    } catch (err) {
      let message = describeError(err);
      if (err instanceof ApiError && err.data && typeof err.data === "object") {
        const data = err.data as { errors?: Array<{ field: string; message: string }> };
        if (data.errors?.length) message += " " + data.errors.map((item) => `${item.field}: ${item.message}`).join("; ");
      }
      setError(message);
    } finally { setBusy(false); }
  }
  function exportResult() {
    if (!result) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify({ case: draft, analysis: result }, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url; link.download = "banking-preflight.json"; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function field(key: keyof Omit<DisbursementCase, "documents" | "invoices" | "currency">, label: string, type = "text") {
    return <label className={styles.field}>{label}<input name={key} value={draft[key]} required type={type}
      min={type === "number" ? (key === "requested_amount" ? "1" : "0") : undefined}
      max={type === "number" ? "999999999999999" : undefined} step={type === "number" ? "1" : undefined}
      maxLength={type === "text" ? 200 : undefined}
      onChange={(e) => update({ ...draft, [key]: e.target.value })} /></label>;
  }
  function invoiceField(invoice: BankingInvoice, index: number, key: keyof BankingInvoice, label: string, type = "text") {
    return <label className={styles.field}>{label}<input name={`invoices.${index}.${key}`} value={invoice[key]} required type={type}
      min={type === "number" ? (key === "amount" ? "1" : "0") : undefined}
      max={type === "number" ? "999999999999999" : undefined} step={type === "number" ? "1" : undefined}
      maxLength={type === "text" ? 200 : undefined}
      onChange={(e) => update({ ...draft, invoices: draft.invoices.map((item, i) => i === index ? { ...item, [key]: e.target.value } : item) })} /></label>;
  }

  return <div className={styles.page}>
    <header className={styles.header}>
      <div><div className={styles.eyebrow}><Landmark size={16} aria-hidden="true" /> BANKING · PILOT</div>
        <h1>Tiền kiểm hồ sơ giải ngân</h1><p>Vốn lưu động doanh nghiệp · Đối chiếu chứng từ và điều kiện trước khi chuyển cán bộ kiểm soát.</p></div>
      <button className="secondary-button" type="button" disabled={busy || !mounted} onClick={sample}>Nạp hồ sơ mẫu</button>
    </header>
    <div className={styles.notice}><strong>Phạm vi thử nghiệm</strong><p>Dữ liệu nhập tay, chỉ hỗ trợ VND. Checklist và luật mẫu cần được ngân hàng xác nhận. Kết quả không phải phê duyệt tín dụng hay lệnh giải ngân. Hồ sơ chưa được lưu trên máy chủ; có thể tải kết quả sau khi kiểm tra.</p></div>
    <div className={styles.layout}>
      <form onSubmit={analyze}>
        <fieldset disabled={busy || !mounted} className={styles.formBody}>
          <section className={styles.card}><h2>01 · Thông tin hồ sơ</h2><div className={styles.grid}>
            {field("case_id", "Mã hồ sơ")}{field("borrower", "Khách hàng vay")}
            {field("borrower_tax_id", "Mã số thuế khách hàng")}{field("beneficiary_tax_id", "Mã số thuế bên thụ hưởng")}
            {field("requested_amount", "Số tiền đề nghị (VND)", "number")}{field("contract_reference", "Số hợp đồng tín dụng")}
            {field("contract_valid_until", "Hợp đồng có hiệu lực đến", "date")}
          </div></section>
          <section className={styles.card}><h2>02 · Hạn mức tham chiếu</h2><p>Nhập số liệu đã đối chiếu với nguồn nội bộ. Dữ liệu này chưa được kết nối trực tiếp với core banking.</p><div className={styles.grid}>
            {field("approved_limit", "Hạn mức được cấp (VND)", "number")}{field("outstanding_amount", "Dư nợ sử dụng hạn mức (VND)", "number")}
            {field("limit_as_of", "Ngày chốt dữ liệu hạn mức", "date")}
          </div></section>
          <section className={styles.card}><h2>03 · Checklist chứng từ</h2><p>Đánh dấu sau khi kiểm tra tài liệu gốc. Đây là xác nhận thủ công về sự hiện diện của chứng từ.</p>
            <div className={styles.checklist}>{documents.map(([key, label]) => <label key={key}><input type="checkbox" checked={draft.documents.includes(key)} onChange={(e) => update({ ...draft, documents: e.target.checked ? [...draft.documents, key] : draft.documents.filter((item) => item !== key) })} />{label}</label>)}</div>
          </section>
          <section className={styles.card}><h2>04 · Hóa đơn làm căn cứ</h2><p>Đối chiếu bên mua, bên bán, ngày lập và phần giá trị chưa tài trợ. Kiểm tra trùng chỉ trong hồ sơ hiện tại.</p>
            {draft.invoices.map((invoice, index) => <div className={styles.invoice} key={index}>
              <div className={styles.row}><h3>Hóa đơn {index + 1}</h3><button type="button" className={styles.textButton} aria-label={`Xóa hóa đơn ${index + 1}`} onClick={() => update({ ...draft, invoices: draft.invoices.filter((_, i) => i !== index) })}><Trash2 size={15} aria-hidden="true" /> Xóa</button></div>
              <div className={styles.grid}>
                {invoiceField(invoice, index, "number", "Số hóa đơn")}{invoiceField(invoice, index, "issued_on", "Ngày lập", "date")}
                {invoiceField(invoice, index, "buyer_tax_id", "Mã số thuế bên mua")}{invoiceField(invoice, index, "seller_tax_id", "Mã số thuế bên bán")}
                {invoiceField(invoice, index, "amount", "Giá trị hóa đơn (VND)", "number")}{invoiceField(invoice, index, "already_financed", "Đã tài trợ (VND)", "number")}
                {invoiceField(invoice, index, "source_reference", "Nguồn đối chiếu (tên tài liệu / trang)")}
              </div>
            </div>)}
            <button type="button" className={styles.textButton} disabled={draft.invoices.length >= 100} onClick={() => update({ ...draft, invoices: [...draft.invoices, emptyInvoice()] })}><Plus size={16} aria-hidden="true" /> Thêm hóa đơn</button>
          </section>
          <button type="submit" className="primary-button"><FileCheck2 size={17} aria-hidden="true" />{busy ? "Đang kiểm tra…" : "Kiểm tra hồ sơ"}</button>
        </fieldset>
      </form>
      <aside className={styles.results} aria-label="Kết quả tiền kiểm" aria-busy={busy}>
        <section className={styles.card}><h2>Kết quả tiền kiểm</h2>
          {error && <div role="alert" className={styles.error}>{error}</div>}
          {!result && <p role="status">{busy ? "Đang đối chiếu hồ sơ với bộ luật pilot…" : "Nhập hồ sơ hoặc nạp dữ liệu mẫu, sau đó chọn Kiểm tra hồ sơ. Kết quả cần được kiểm tra lại sau mỗi lần sửa dữ liệu."}</p>}
          {result && <>
            <div className={styles.row} role="status"><strong>{result.case_id}</strong><StatusBadge status={result.status} /></div>
            <dl className={styles.metrics}><div><dt>Hạn mức còn lại</dt><dd>{money(Number(result.available_limit))}</dd></div><div><dt>Giá trị hóa đơn còn lại qua kiểm tra</dt><dd>{money(Number(result.eligible_invoice_amount))}</dd></div></dl>
            <p>Luật {result.policy_version} · Ngày kiểm tra {result.evaluated_on}</p>
            {result.findings.length === 0 ? <p>Đã qua các kiểm tra pilot. Cán bộ cần xác minh chứng từ và điều kiện nghiệp vụ trước bước phê duyệt.</p> : <h3>{result.findings.length} vấn đề cần xử lý</h3>}
            {result.findings.map((finding, index) => <article className={styles.finding} key={`${finding.code}-${index}`}>
              <StatusBadge status={finding.severity === "error" ? "Blocked" : "Review required"} />
              <h3>{explanations[finding.code]?.[0] ?? finding.code}</h3><p>{explanations[finding.code]?.[1]}</p>
              <details><summary>Xem căn cứ đối chiếu</summary><p>Mã kiểm tra: {finding.code}</p><p>Trường dữ liệu: {finding.fields.join(", ")}</p><dl>{Object.entries(finding.evidence).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl></details>
            </article>)}
            <button type="button" className="secondary-button" onClick={exportResult}><Download size={16} aria-hidden="true" /> Tải hồ sơ và kết quả</button>
          </>}
        </section>
      </aside>
    </div>
  </div>;
}
