"use client";

import { useMemo, useState } from "react";
import { Download } from "lucide-react";

import { FilterSelect } from "@/components/common/FilterSelect";
import { SearchFilter } from "@/components/common/SearchFilter";
import { auditEntries } from "@/app/lib/seed";
import type { ActivityEventType } from "@/app/lib/types";
import { useRipple } from "@/app/lib/useRipple";

type TypeFilter = "all" | ActivityEventType;

const TYPE_OPTIONS = [
  { label: "All events", value: "all" },
  { label: "Human decisions", value: "human" },
  { label: "System events", value: "system" },
];

export function AuditView() {
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const { createRipple } = useRipple();

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return auditEntries.filter((entry) => {
      if (typeFilter !== "all" && entry.type !== typeFilter) {
        return false;
      }
      if (!needle) {
        return true;
      }
      return [entry.order, entry.actor, entry.event].some((field) =>
        field.toLowerCase().includes(needle),
      );
    });
  }, [query, typeFilter]);

  return (
    <div className="page simple-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">GOVERNANCE</p>
          <h1>Audit log</h1>
          <p>
            Immutable evidence for extraction, validation, and human decisions.
          </p>
        </div>
        <button
          className="secondary-button interactive"
          onClick={createRipple}
          style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
        >
          <Download size={15} strokeWidth={2} />
          <span>Export CSV</span>
        </button>
      </div>
      <section className="content-card audit-card">
        <div className="panel-toolbar">
          <SearchFilter
            value={query}
            onChange={setQuery}
            placeholder="Search order, person, or event"
          />
          <FilterSelect
            ariaLabel="Filter by event type"
            value={typeFilter}
            onChange={(value) => setTypeFilter(value as TypeFilter)}
            options={TYPE_OPTIONS}
          />
        </div>
        {rows.map((item) => (
          <div className="audit-row interactive" key={item.id}>
            <time className="tabular-nums">{item.time}</time>
            <span className="audit-dot" />
            <div>
              <strong>{item.event}</strong>
              <small>{item.detail}</small>
            </div>
            <span>{item.actor}</span>
            <b className="tabular-nums">{item.order}</b>
          </div>
        ))}
      </section>
    </div>
  );
}