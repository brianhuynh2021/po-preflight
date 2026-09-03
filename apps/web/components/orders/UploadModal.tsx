"use client";

import { useEffect, useRef } from "react";

export function UploadModal({
  onClose,
  onFile,
}: {
  onClose: () => void;
  onFile: (fileName: string, file?: File) => void;
}) {
  const modalRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
      if (e.key === "Tab" && modalRef.current) {
        const focusables = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
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

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        ref={modalRef}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <div className="modal-icon">↑</div>
        <h2 id="upload-title">Upload a purchase order</h2>
        <p>
          Preflight will extract the order and run company validation rules.
          You will review the result before any approval.
        </p>
        <label className="drop-zone">
          <input
            type="file"
            accept=".pdf,.csv,.json,.txt,.xlsx,.xls,.xlsm,.png,.jpg,.jpeg"
            onChange={(event) => {
              if (event.target.files?.length) {
                onFile(event.target.files[0].name, event.target.files[0]);
              }
            }}
          />

          <span className="upload-symbol">＋</span>
          <strong>Drop a file here or choose a file</strong>
          <small>PDF, Excel (.xlsx/.xls), CSV, JSON, PNG/Ảnh chụp, hoặc TXT · Maximum 20 MB</small>

        </label>
        <div className="modal-note">
          <span>i</span>
          <p>
            <strong>Human review is always required.</strong>
            <br />
            Preflight never creates an ERP order automatically in this
            prototype.
          </p>
        </div>
      </section>
    </div>
  );
}
