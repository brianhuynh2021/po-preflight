"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  Download,
  FileUp,
  Plus,
  RefreshCw,
  Trash2,
  Users,
  X,
  CreditCard,
  Tag,
} from "lucide-react";

import { SearchFilter } from "@/components/common/SearchFilter";
import { money } from "@/app/lib/derive";
import { api } from "@/app/lib/api/client";
import { useRipple } from "@/app/lib/useRipple";
import type { CustomerMaster } from "@/app/lib/types";

const SEED_CUSTOMERS: CustomerMaster[] = [
  {
    code: "CUST-VINGROUP",
    name: "Tập đoàn Vingroup - Công ty CP",
    normalized_name: "vingroup",
    tax_code: "0101245486",
    tier: "VIP",
    aliases: ["Vingroup", "VinGroup Retail", "Tập đoàn Vingroup", "Vingroup Infrastructure"],
  },
  {
    code: "CUST-NORTHSTAR",
    name: "Northstar Retail Vietnam LLC",
    normalized_name: "northstar retail vietnam",
    tax_code: "0314987654",
    tier: "PLATINUM",
    aliases: ["Northstar Retail", "Northstar VN", "Công ty TNHH Bán Lẻ Northstar"],
  },
  {
    code: "CUST-ACME",
    name: "Acme Corporation Vietnam",
    normalized_name: "acme",
    tax_code: "0109876543",
    tier: "STANDARD",
    aliases: ["Acme Corp", "Acme Vietnam", "TNHH Acme"],
  },
  {
    code: "CUST-ALPHA",
    name: "Alpha Technology Solutions",
    normalized_name: "alpha technology",
    tax_code: "0312345678",
    tier: "STANDARD",
    aliases: ["Alpha Tech", "Alpha Corp"],
  },
];

export function CustomerMasterView() {
  const [customers, setCustomers] = useState<CustomerMaster[]>(SEED_CUSTOMERS);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [query, setQuery] = useState("");
  const [tierFilter, setTierFilter] = useState("all");
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerMaster | null>(null);
  const [customerDetail, setCustomerDetail] = useState<{
    pricing?: Array<{ sku: string; contract_price: number; min_quantity: number; discount_percent: number }>;
    credit?: { credit_limit: number; outstanding_balance: number; overdue_balance: number; status: string } | null;
    recent_orders?: Array<{ id: number; po_number: string; status: string; total: number }>;
  } | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // Modal create/edit
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [formData, setFormData] = useState({
    code: "",
    name: "",
    tax_code: "",
    tier: "STANDARD",
    aliases: "",
  });

  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { createRipple } = useRipple();

  const fetchCustomers = useCallback(async () => {
    setIsSyncing(true);
    try {
      const data = await api.customers.list();
      if (Array.isArray(data) && data.length > 0) {
        setCustomers(data);
      }
    } catch {
      // Fallback to local state
    } finally {
      setIsSyncing(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchCustomers();
  }, [fetchCustomers]);

  const handleSelectCustomer = async (cust: CustomerMaster) => {
    setSelectedCustomer(cust);
    setIsLoadingDetail(true);
    try {
      const detail = await api.customers.get(cust.code);
      setCustomerDetail(detail);
    } catch {
      setCustomerDetail(null);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleSaveCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const aliasList = formData.aliases
        .split(";")
        .map((a) => a.trim())
        .filter(Boolean);

      if (modalMode === "create") {
        await api.customers.create({
          code: formData.code.trim().toUpperCase(),
          name: formData.name.trim(),
          tax_code: formData.tax_code.trim() || undefined,
          tier: formData.tier,
          aliases: aliasList,
        });
        setFeedback({ type: "success", message: `Đã tạo mới khách hàng '${formData.name}' thành công.` });
      } else {
        await api.customers.update(formData.code, {
          name: formData.name.trim(),
          tax_code: formData.tax_code.trim() || undefined,
          tier: formData.tier,
          aliases: aliasList,
        });
        setFeedback({ type: "success", message: `Đã cập nhật hồ sơ khách hàng '${formData.code}' thành công.` });
      }
      setShowModal(false);
      await fetchCustomers();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Thao tác thất bại";
      setFeedback({ type: "error", message: `Lỗi: ${msg}` });
    }
  };

  const handleDelete = async (code: string) => {
    if (!confirm(`Bạn có chắc muốn xóa khách hàng '${code}' khỏi cơ sở dữ liệu?`)) return;
    try {
      await api.customers.delete(code);
      setFeedback({ type: "success", message: `Đã xóa khách hàng '${code}'.` });
      if (selectedCustomer?.code === code) {
        setSelectedCustomer(null);
      }
      await fetchCustomers();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Xóa thất bại";
      setFeedback({ type: "error", message: `Lỗi: ${msg}` });
    }
  };

  const handleCSVImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsImporting(true);
    try {
      const res = await api.customers.importCSV(file);
      setFeedback({
        type: "success",
        message: `Đã nhập thành công ${res.imported_count} khách hàng từ CSV.`,
      });
      await fetchCustomers();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Lỗi nhập file CSV";
      setFeedback({ type: "error", message: `Lỗi: ${msg}` });
    } finally {
      setIsImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const filteredCustomers = useMemo(() => {
    const q = query.toLowerCase().trim();
    return customers.filter((c) => {
      const aliases = c.aliases || [];
      const matchSearch =
        !q ||
        c.code.toLowerCase().includes(q) ||
        c.name.toLowerCase().includes(q) ||
        (c.tax_code && c.tax_code.toLowerCase().includes(q)) ||
        aliases.some((a) => a.toLowerCase().includes(q));

      const matchTier = tierFilter === "all" || c.tier === tierFilter;
      return matchSearch && matchTier;
    });
  }, [customers, query, tierFilter]);

  const stats = useMemo(() => {
    const total = customers.length;
    const vip = customers.filter((c) => c.tier === "VIP" || c.tier === "PLATINUM").length;
    const totalAliases = customers.reduce((acc, c) => acc + (c.aliases?.length || 0), 0);
    return { total, vip, totalAliases };
  }, [customers]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50 flex items-center gap-2">
            <Building2 className="h-7 w-7 text-primary-600 dark:text-primary-400" />
            Hồ sơ Khách hàng & Định danh (Master Customer)
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            Quản lý mã định danh khách hàng, mã số thuế, chính sách giá hợp đồng và học alias tự động.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleCSVImport}
            accept=".csv"
            style={{ display: "none" }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isImporting}
            className="btn btn-secondary flex items-center gap-2"
          >
            <FileUp className="h-4 w-4" />
            <span>{isImporting ? "Đang nhập..." : "Nhập CSV"}</span>
          </button>

          <a
            href="/api/v1/customers/export-csv"
            download="customers_master.csv"
            className="btn btn-secondary flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            <span>Xuất CSV</span>
          </a>

          <button
            onClick={() => {
              setModalMode("create");
              setFormData({ code: "", name: "", tax_code: "", tier: "STANDARD", aliases: "" });
              setShowModal(true);
            }}
            onMouseDown={createRipple}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            <span>Thêm khách hàng</span>
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="card p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{stats.total}</div>
            <div className="text-xs text-neutral-500 font-medium">Tổng khách hàng Master</div>
          </div>
        </div>

        <div className="card p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center text-amber-600 dark:text-amber-400">
            <Tag className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{stats.vip}</div>
            <div className="text-xs text-neutral-500 font-medium">Khách hàng VIP & Platinum</div>
          </div>
        </div>

        <div className="card p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
            <Building2 className="h-6 w-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{stats.totalAliases}</div>
            <div className="text-xs text-neutral-500 font-medium">Bí danh nhận diện (Aliases)</div>
          </div>
        </div>
      </div>

      {/* Feedback banner */}
      {feedback && (
        <div
          className={`p-4 rounded-xl flex items-center justify-between gap-3 ${
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-800"
              : "bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200 border border-rose-200 dark:border-rose-800"
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === "success" ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <AlertCircle className="h-5 w-5 text-rose-600 dark:text-rose-400" />
            )}
            <span className="text-sm font-medium">{feedback.message}</span>
          </div>
          <button
            onClick={() => setFeedback(null)}
            className="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Main layout with Table & Detail Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Table column */}
        <div className={`card overflow-hidden ${selectedCustomer ? "lg:col-span-2" : "lg:col-span-3"}`}>
          <div className="p-4 border-b border-neutral-200 dark:border-neutral-800 flex flex-col sm:flex-row gap-3 justify-between items-center bg-neutral-50/50 dark:bg-neutral-900/50">
            <div className="w-full sm:w-80">
              <SearchFilter
                value={query}
                onChange={setQuery}
                placeholder="Tìm theo tên, mã, MST, alias..."
              />
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              <select
                value={tierFilter}
                onChange={(e) => setTierFilter(e.target.value)}
                className="input text-sm py-1.5"
              >
                <option value="all">Tất cả phân hạng</option>
                <option value="VIP">VIP</option>
                <option value="PLATINUM">PLATINUM</option>
                <option value="GOLD">GOLD</option>
                <option value="STANDARD">STANDARD</option>
              </select>

              <button
                onClick={fetchCustomers}
                disabled={isSyncing}
                className="btn btn-ghost p-2 text-neutral-500"
                title="Làm mới"
              >
                <RefreshCw className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-neutral-50 dark:bg-neutral-900/80 text-xs uppercase tracking-wider text-neutral-500 border-b border-neutral-200 dark:border-neutral-800">
                <tr>
                  <th className="px-4 py-3">Mã & Tên Pháp Nhân</th>
                  <th className="px-4 py-3">Mã số thuế</th>
                  <th className="px-4 py-3">Phân hạng</th>
                  <th className="px-4 py-3">Aliases nhận diện</th>
                  <th className="px-4 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
                {filteredCustomers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-neutral-400">
                      Không tìm thấy khách hàng phù hợp.
                    </td>
                  </tr>
                ) : (
                  filteredCustomers.map((cust) => {
                    const isSelected = selectedCustomer?.code === cust.code;
                    return (
                      <tr
                        key={cust.code}
                        onClick={() => handleSelectCustomer(cust)}
                        className={`cursor-pointer transition-colors hover:bg-neutral-50 dark:hover:bg-neutral-800/50 ${
                          isSelected ? "bg-primary-50/50 dark:bg-primary-950/20" : ""
                        }`}
                      >
                        <td className="px-4 py-3">
                          <div className="font-semibold text-neutral-900 dark:text-neutral-50">{cust.name}</div>
                          <div className="text-xs text-neutral-400 font-mono">{cust.code}</div>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-neutral-600 dark:text-neutral-300">
                          {cust.tax_code || "—"}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`badge text-xs font-semibold ${
                              cust.tier === "VIP"
                                ? "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200"
                                : cust.tier === "PLATINUM"
                                ? "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200"
                                : "bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
                            }`}
                          >
                            {cust.tier}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1 max-w-xs">
                            {(cust.aliases || []).slice(0, 3).map((a, idx) => (
                              <span
                                key={idx}
                                className="text-xs bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 px-2 py-0.5 rounded"
                              >
                                {a}
                              </span>
                            ))}
                            {(cust.aliases || []).length > 3 && (
                              <span className="text-xs text-neutral-400 font-medium">
                                +{(cust.aliases || []).length - 3}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => {
                                setModalMode("edit");
                                setFormData({
                                  code: cust.code,
                                  name: cust.name,
                                  tax_code: cust.tax_code || "",
                                  tier: cust.tier || "STANDARD",
                                  aliases: (cust.aliases || []).join("; "),
                                });
                                setShowModal(true);
                              }}
                              className="text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400 font-medium"
                            >
                              Sửa
                            </button>
                            <button
                              onClick={() => handleDelete(cust.code)}
                              className="text-neutral-400 hover:text-rose-600 transition-colors"
                              title="Xóa khách hàng"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Detail column */}
        {selectedCustomer && (
          <div className="card p-6 space-y-6 lg:col-span-1">
            <div className="flex items-start justify-between">
              <div>
                <span className="badge text-xs font-semibold bg-primary-100 text-primary-800 dark:bg-primary-900/40 dark:text-primary-300">
                  {selectedCustomer.tier || "STANDARD"}
                </span>
                <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-50 mt-1">
                  {selectedCustomer.name}
                </h2>
                <div className="text-xs text-neutral-400 font-mono mt-0.5">Mã: {selectedCustomer.code}</div>
              </div>
              <button
                onClick={() => setSelectedCustomer(null)}
                className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* General info */}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span className="text-neutral-500">Mã số thuế:</span>
                <span className="font-mono font-medium">{selectedCustomer.tax_code || "Chưa cập nhật"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span className="text-neutral-500">Tên chuẩn hóa:</span>
                <span className="font-mono text-xs">{selectedCustomer.normalized_name}</span>
              </div>
            </div>

            {/* Aliases */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">
                Bí danh nhận diện (Aliases)
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {(selectedCustomer.aliases || []).map((al, idx) => (
                  <span
                    key={idx}
                    className="text-xs bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 px-2.5 py-1 rounded-md"
                  >
                    {al}
                  </span>
                ))}
              </div>
            </div>

            {/* Credit info */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2 flex items-center gap-1.5">
                <CreditCard className="h-4 w-4" />
                Hạn mức & Công nợ
              </h3>
              {isLoadingDetail ? (
                <div className="text-xs text-neutral-400 py-2">Đang tải hồ sơ công nợ...</div>
              ) : customerDetail?.credit ? (
                <div className="bg-neutral-50 dark:bg-neutral-900/50 p-3 rounded-xl space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Hạn mức tín dụng:</span>
                    <span className="font-semibold">{money(customerDetail.credit.credit_limit)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Dư nợ hiện tại:</span>
                    <span className="font-semibold">{money(customerDetail.credit.outstanding_balance)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Nợ quá hạn:</span>
                    <span className={`font-semibold ${customerDetail.credit.overdue_balance > 0 ? "text-rose-600" : ""}`}>
                      {money(customerDetail.credit.overdue_balance)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Trạng thái công nợ:</span>
                    <span className="badge text-[10px] font-semibold">{customerDetail.credit.status}</span>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-neutral-400 italic">Chưa cấu hình hồ sơ công nợ riêng.</div>
              )}
            </div>

            {/* Contract pricing */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2 flex items-center gap-1.5">
                <Tag className="h-4 w-4" />
                Giá hợp đồng riêng ({customerDetail?.pricing?.length || 0})
              </h3>
              {customerDetail?.pricing && customerDetail.pricing.length > 0 ? (
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {customerDetail.pricing.map((p, idx) => (
                    <div
                      key={idx}
                      className="flex justify-between items-center text-xs p-2 rounded bg-neutral-50 dark:bg-neutral-900/40"
                    >
                      <div>
                        <span className="font-mono font-medium">{p.sku}</span>
                        {p.min_quantity > 1 && (
                          <span className="text-neutral-400 ml-1">(≥ {p.min_quantity})</span>
                        )}
                      </div>
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                        {money(p.contract_price)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-neutral-400 italic">Áp dụng bảng giá niêm yết chuẩn.</div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create / Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="card max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-neutral-200 dark:border-neutral-800 pb-3">
              <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-50">
                {modalMode === "create" ? "Thêm mới khách hàng Master" : `Chỉnh sửa: ${formData.code}`}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-neutral-400 hover:text-neutral-600">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSaveCustomer} className="space-y-4 text-sm">
              {modalMode === "create" && (
                <div>
                  <label className="block text-xs font-semibold uppercase text-neutral-500 mb-1">
                    Mã khách hàng (Customer Code) *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="VD: CUST-VINFAST"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="input w-full font-mono uppercase"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold uppercase text-neutral-500 mb-1">
                  Tên pháp nhân đầy đủ *
                </label>
                <input
                  type="text"
                  required
                  placeholder="VD: Công ty Cổ phần Sản xuất và Kinh doanh VinFast"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase text-neutral-500 mb-1">
                    Mã số thuế (MST)
                  </label>
                  <input
                    type="text"
                    placeholder="VD: 0108987654"
                    value={formData.tax_code}
                    onChange={(e) => setFormData({ ...formData, tax_code: e.target.value })}
                    className="input w-full font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-neutral-500 mb-1">
                    Phân hạng đối tác
                  </label>
                  <select
                    value={formData.tier}
                    onChange={(e) => setFormData({ ...formData, tier: e.target.value })}
                    className="input w-full"
                  >
                    <option value="VIP">VIP</option>
                    <option value="PLATINUM">PLATINUM</option>
                    <option value="GOLD">GOLD</option>
                    <option value="STANDARD">STANDARD</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-neutral-500 mb-1">
                  Bí danh nhận diện (Aliases - phân cách bằng dấu chấm phẩy ;)
                </label>
                <input
                  type="text"
                  placeholder="VD: VinFast; VinFast Auto; VF Vietnam"
                  value={formData.aliases}
                  onChange={(e) => setFormData({ ...formData, aliases: e.target.value })}
                  className="input w-full"
                />
                <p className="text-[11px] text-neutral-400 mt-1">
                  Khi PO gửi đến có các tên này, hệ thống sẽ tự động map chính xác về khách hàng này.
                </p>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-neutral-200 dark:border-neutral-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="btn btn-secondary"
                >
                  Hủy
                </button>
                <button type="submit" className="btn btn-primary">
                  {modalMode === "create" ? "Tạo khách hàng" : "Lưu thay đổi"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
