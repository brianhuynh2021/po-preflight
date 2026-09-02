"use client";

import { Plus, ShieldAlert, AlertTriangle } from "lucide-react";
import { rules } from "@/app/lib/seed";
import { useRipple } from "@/app/lib/useRipple";

export function RulesView() {
  const { createRipple } = useRipple();

  return (
    <div className="page simple-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">POLICY CONTROL</p>
          <h1>Validation rules</h1>
          <p>Deterministic controls applied to every normalized order.</p>
        </div>
        <button
          className="primary-button interactive"
          onClick={createRipple}
          style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
        >
          <Plus size={16} strokeWidth={2.2} />
          <span>Add rule</span>
        </button>
      </div>
      <section className="content-card rules-card">
        {rules.map((rule) => (
          <div className="rule-row interactive" key={rule.name}>
            <span
              className={`rule-symbol ${rule.severity.toLowerCase()}`}
              style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
            >
              {rule.severity === "Block" ? (
                <ShieldAlert size={16} strokeWidth={2.2} />
              ) : (
                <AlertTriangle size={15} strokeWidth={2.2} />
              )}
            </span>
            <div>
              <strong>{rule.name}</strong>
              <p>{rule.description}</p>
            </div>
            <span
              className={`severity severity-${rule.severity.toLowerCase()}`}
            >
              {rule.severity}
            </span>
            <span className="rule-owner">{rule.owner}</span>
            <label className="switch">
              <input type="checkbox" defaultChecked />
              <span />
            </label>
          </div>
        ))}
      </section>
    </div>
  );
}
