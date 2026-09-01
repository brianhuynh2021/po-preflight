"use client";

import { rules } from "@/data/rules";

export function RulesView() {
  return (
    <div className="page simple-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">POLICY CONTROL</p>
          <h1>Validation rules</h1>
          <p>Deterministic controls applied to every normalized order.</p>
        </div>
        <button className="primary-button">＋ Add rule</button>
      </div>
      <section className="content-card rules-card">
        {rules.map((rule) => (
          <div className="rule-row" key={rule.name}>
            <span className={`rule-symbol ${rule.severity.toLowerCase()}`}>
              {rule.severity === "Block" ? "×" : "!"}
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
