"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useMounted } from "@/app/lib/useMounted";
import {
  UploadCloud,
  X,
  FileText,
  FileSpreadsheet,
  FileImage,
  ShieldCheck,
  Sparkles,
  ArrowRight,
} from "lucide-react";

interface UploadModalProps {
  onClose: () => void;
  onFile: (fileName: string, file?: File) => void;
}

const PRESET_SAMPLES = [
  {
    id: "northstar",
    name: "northstar-po-10428.pdf",
    title: "Đơn bán lẻ Northstar Retail",
    desc: "Đơn đặt hàng thiết bị mạng (Có cảnh báo chênh lệch giá SKU)",
    badge: "PDF Chuẩn",
    icon: FileText,
    type: "application/pdf",
    content: "PO-10428 Northstar Retail Customer Order Payload",
  },
  {
    id: "acme",
    name: "acme-batch-order.xlsx",
    title: "Bảng kê lô hàng Acme Technology",
    desc: "Đơn hàng linh kiện viễn thông (Phát hiện vượt hạn mức tín dụng)",
    badge: "Excel .xlsx",
    icon: FileSpreadsheet,
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    content: "Acme Technology Batch Order 2026",
  },
  {
    id: "scan",
    name: "invoice-scan-hd2026.png",
    title: "Hóa đơn giấy quét ảnh (Scan OCR)",
    desc: "Chứng từ bóc tách tự động bằng trí tuệ nhân tạo OCR",
    badge: "Ảnh Scan AI",
    icon: FileImage,
    type: "image/png",
    content: "Invoice Scan OCR Sample Data",
  },
];

export function UploadModal({ onClose, onFile }: UploadModalProps) {
  const mounted = useMounted();
  const modalRef = useRef<HTMLElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
      if (e.key === "Tab" && modalRef.current) {
        const focusables = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (focusables.length > 0) {
          const first = focusables[0];
          const last = focusables[focusables.length - 1];
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      onFile(droppedFile.name, droppedFile);
    }
  };

  const handleSelectPreset = (sample: (typeof PRESET_SAMPLES)[number]) => {
    const blob = new Blob([sample.content], { type: sample.type });
    const file = new File([blob], sample.name, { type: sample.type });
    onFile(sample.name, file);
  };

  if (!mounted) return null;

  return createPortal(
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        ref={modalRef}
        className="modal upload-modal-v2"
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        {/* Header Bar */}
        <div className="modal-header-v2">
          <div className="modal-icon-badge">
            <UploadCloud size={22} strokeWidth={2.2} />
          </div>
          <div className="modal-header-text">
            <h2 id="upload-title">Tải lên đơn đặt hàng (Purchase Order)</h2>
            <p>
              Preflight tự động bóc tách dữ liệu, đối chiếu danh mục sản phẩm và kiểm tra quy tắc kinh doanh tức thì.
            </p>
          </div>
          <button
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Đóng cửa sổ"
            type="button"
          >
            <X size={18} />
          </button>
        </div>

        {/* Scrollable Body Content */}
        <div className="modal-body-v2">
          {/* Main Dropzone */}
          <div
            className={`drop-zone-v2 ${isDragging ? "dragging" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                fileInputRef.current?.click();
              }
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              style={{ display: "none" }}
              accept=".pdf,.csv,.json,.txt,.xlsx,.xls,.xlsm,.png,.jpg,.jpeg"
              onChange={(event) => {
                if (event.target.files?.length) {
                  onFile(event.target.files[0].name, event.target.files[0]);
                }
              }}
            />

            <div className="dropzone-icon-circle">
              <UploadCloud size={28} className="dropzone-cloud-icon" />
            </div>
            <strong className="dropzone-title">Kéo thả tệp PO vào đây hoặc bấm để chọn tệp</strong>
            <span className="dropzone-hint">
              Hỗ trợ định dạng PDF, Excel (.xlsx/.xls), CSV, JSON, PNG/Ảnh scan, hoặc TXT · Tối đa 20 MB
            </span>
          </div>

          {/* Preset Demo Samples - 1 Click Experience */}
          <div className="preset-samples-section">
            <div className="preset-section-header">
              <div className="preset-header-title">
                <Sparkles size={15} className="sparkle-icon" />
                <span>Hoặc thử nghiệm nhanh với dữ liệu mẫu (1-Click Test):</span>
              </div>
              <span className="preset-tag">Demo Sandbox</span>
            </div>

            <div className="preset-samples-grid">
              {PRESET_SAMPLES.map((sample) => {
                const IconComp = sample.icon;
                return (
                  <button
                    key={sample.id}
                    type="button"
                    className="preset-sample-card"
                    onClick={() => handleSelectPreset(sample)}
                  >
                    <div className="preset-card-icon">
                      <IconComp size={20} />
                    </div>
                    <div className="preset-card-content">
                      <div className="preset-card-top">
                        <strong className="preset-card-title">{sample.title}</strong>
                        <span className="preset-card-badge">{sample.badge}</span>
                      </div>
                      <span className="preset-card-desc">{sample.desc}</span>
                      <span className="preset-card-filename">{sample.name}</span>
                    </div>
                    <ArrowRight size={14} className="preset-card-arrow" />
                  </button>
                );
              })}
            </div>
          </div>

          {/* Safety & Compliance Notice */}
          <div className="modal-safety-notice">
            <ShieldCheck size={18} className="safety-icon" />
            <div className="safety-text">
              <strong>Nguyên tắc kiểm soát an toàn con người (Human-in-the-Loop):</strong>
              <p>
                PO Preflight không tự ý đẩy đơn hàng lên ERP khi chưa có quyết định phê duyệt chính thức từ người có thẩm quyền.
              </p>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="modal-footer-v2">
          <button type="button" className="secondary-button" onClick={onClose}>
            Hủy bỏ
          </button>
          <button
            type="button"
            className="primary-button cta-button"
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadCloud size={16} />
            <span>Duyệt tệp từ máy tính</span>
          </button>
        </div>
      </section>
    </div>,
    document.body,
  );
}
