"use client";

import Link from "next/link";

import { useAppState } from "@/components/app/AppStateProvider";
import { money } from "@/app/lib/derive";

export function OverviewView() {
  const { orders } = useAppState();
  const attention = orders.filter(
    (order) =>
      order.status === "Review required" || order.status === "Blocked",
  );

  return (
    <div className="page simple-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">GOOD MORNING, MAYA</p>
          <h1>Operations overview</h1>
          <p>Two orders need attention. Everything else is moving normally.</p>
        </div>
        <Link className="primary-button" href="/orders">
          ＋ Upload purchase order
        </Link>
      </div>
      <div className="overview-hero">
        <div>
          <span className="overview-label">TODAY&apos;S PRIORITY</span>
          <h2>
            Resolve two order exceptions before the 2:00 PM fulfillment
            cut-off.
          </h2>
          <p>One price and inventory review, and one blocked catalog item.</p>
          <Link className="light-button" href="/orders">
            Review priority orders →
          </Link>
        </div>
        <div className="radial">
          <strong>86%</strong>
          <span>
            straight-through
            <br />
            validation
          </span>
        </div>
      </div>
      <div className="overview-columns">
        <section className="content-card">
          <div className="card-heading">
            <div>
              <h2>Attention queue</h2>
              <p>Prioritized by business impact</p>
            </div>
            <Link href="/orders" className="text-button">
              View all
            </Link>
          </div>
          {attention.map((order) => (
            <Link className="attention-row" key={order.id} href="/orders">
              <span
                className={`attention-icon ${order.status === "Blocked" ? "red" : "amber"}`}
              >
                {order.status === "Blocked" ? "×" : "!"}
              </span>
              <span>
                <strong>
                  {order.id} · {order.customer}
                </strong>
                <small>
                  {order.findings.length} validation{" "}
                  {order.findings.length === 1 ? "finding" : "findings"}
                </small>
              </span>
              <b>{money(order.value, order.currency)}</b>
              <span>→</span>
            </Link>
          ))}
        </section>
        <section className="content-card">
          <div className="card-heading">
            <div>
              <h2>Weekly flow</h2>
              <p>Processed purchase orders</p>
            </div>
            <span className="positive">+18%</span>
          </div>
          <div className="bar-chart">
            <div>
              <i style={{ height: "42%" }} />
              <small>Mon</small>
            </div>
            <div>
              <i style={{ height: "60%" }} />
              <small>Tue</small>
            </div>
            <div>
              <i style={{ height: "54%" }} />
              <small>Wed</small>
            </div>
            <div>
              <i style={{ height: "78%" }} />
              <small>Thu</small>
            </div>
            <div>
              <i className="today" style={{ height: "66%" }} />
              <small>Fri</small>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
