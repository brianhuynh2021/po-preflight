"use client";

export function UploadModal({
  onClose,
  onFile,
}: {
  onClose: () => void;
  onFile: (fileName: string) => void;
}) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
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
            accept=".pdf,.csv,.json,.txt,.xlsx,.xls,.xlsm"
            onChange={(event) => {
              if (event.target.files?.length) {
                onFile(event.target.files[0].name);
              }
            }}
          />
          <span className="upload-symbol">＋</span>
          <strong>Drop a file here or choose a file</strong>
          <small>PDF, Excel (.xlsx/.xls), CSV, JSON, or TXT · Maximum 20 MB</small>

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
