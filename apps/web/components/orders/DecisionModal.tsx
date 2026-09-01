"use client";

import type { PurchaseOrder } from "@/app/lib/types";

export function DecisionModal({
  order,
  note,
  onNoteChange,
  onClose,
  onConfirm,
}: {
  order: PurchaseOrder;
  note: string;
  onNoteChange: (value: string) => void;
  onClose: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal decision-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="decision-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <span className="review-label">APPROVAL DECISION</span>
        <h2 id="decision-title">Approve {order.id}?</h2>
        <p>
          This decision will be attributed to Maya Chen and added to the
          permanent audit history.
        </p>
        {order.findings.length ? (
          <div className="decision-warning">
            <strong>
              {order.findings.length} validation findings acknowledged
            </strong>
            <span>
              You are approving this order with documented exceptions.
            </span>
          </div>
        ) : null}
        <label className="note-field">
          <span>
            Decision note{" "}
            {order.findings.length ? "(required)" : "(optional)"}
          </span>
          <textarea
            value={note}
            onChange={(event) => onNoteChange(event.target.value)}
            placeholder="Explain the reason for this decision..."
            rows={4}
          />
        </label>
        <div className="modal-actions">
          <button className="secondary-button" onClick={onClose}>
            Cancel
          </button>
          <button
            className="approve-button"
            disabled={order.findings.length > 0 && !note.trim()}
            onClick={onConfirm}
          >
            Confirm approval
          </button>
        </div>
      </section>
    </div>
  );
}
