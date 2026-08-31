import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { Panel } from "../components/Panel";
import { Kpi } from "../components/Kpi";
import { WorldMap } from "../components/WorldMap";
import { DataTable, type Column } from "../components/DataTable";
import { Seg } from "../components/Seg";
import { EChart } from "../lib/chart";
import { cssVar } from "../lib/theme";
import { money } from "../lib/format";
import {
  ACTIVITY,
  KPIS,
  TRAFFIC_SOURCES,
  TRAFFIC_TOTAL,
  revenueSeries,
} from "../data/meta";
import { generateOrders, ordersByCity, type Order } from "../data/orders";

const ORDERS = generateOrders();

const statusTone: Record<string, "pos" | "warn" | "neg"> = {
  Paid: "pos",
  Pending: "warn",
  Refunded: "neg",
};

export function Dashboard() {
  const [range, setRange] = useState<"30d" | "90d" | "12m">("12m");
  const [pin, setPin] = useState<string | undefined>(undefined);
  const [page, setPage] = useState(1);

  const hotpoints = useMemo(() => ordersByCity(ORDERS, pin), [pin]);

  const filtered = useMemo(
    () => (pin ? ORDERS.filter((o) => o.city === pin) : ORDERS),
    [pin],
  );

  const rev = useMemo(() => revenueSeries(range), [range]);

  const pinSum = filtered.reduce((a, o) => a + o.total, 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div className="kpis">
        {KPIS.map((k, i) => (
          <Kpi key={k.lbl} kpi={k} index={i} />
        ))}
      </div>

      <Panel title="Global activity">
        <WorldMap
          hotspots={hotpoints}
          pin={pin}
          onPick={(c) => {
            setPin(c ?? undefined);
            setPage(1);
          }}
        />
        <div
          style={{
            display: "flex",
            gap: 8,
            padding: "0 20px 14px",
            flexWrap: "wrap",
          }}>
          {pin ? (
            <button
              className="geochip"
              type="button"
              onClick={() => {
                setPin(undefined);
                setPage(1);
              }}>
              {pin} <b>{Math.round(pinSum / 100)}</b>
              <u title="Clear">×</u>
            </button>
          ) : (
            <span className="faint" style={{ fontSize: 11.5 }}>
              Click a hotspot to filter by city
            </span>
          )}
        </div>
      </Panel>

      <div className="g2">
        <Panel
          title="Revenue"
          tools={
            <>
              <span className="faint" style={{ fontSize: 11.5 }}>
                vs previous period
              </span>
              <Seg
                id="rangeSeg"
                options={[
                  { value: "30d", label: "30d" },
                  { value: "90d", label: "90d" },
                  { value: "12m", label: "12m" },
                ]}
                value={range}
                onChange={setRange}
              />
            </>
          }>
          <EChart
            id="revChart"
            className="chart fill"
            deps={[range]}
            build={() => {
              const accent = cssVar("--accent", "#ff7a1a");
              const faint = cssVar("--faint", "#a09a90");
              return {
                tooltip: {
                  trigger: "axis",
                  valueFormatter: (value) => money(Number(value)),
                },
                legend: {
                  right: 0,
                  top: 0,
                  itemWidth: 7,
                  itemHeight: 7,
                  icon: "circle",
                },
                grid: { left: 46, right: 12, top: 26, bottom: 22 },
                xAxis: {
                  type: "category",
                  data: rev.labels,
                  boundaryGap: false,
                  axisLabel: {
                    interval: Math.max(0, Math.floor(rev.labels.length / 7)),
                  },
                },
                yAxis: {
                  type: "value",
                  splitLine: { show: false },
                  axisLabel: {
                    fontFamily: cssVar("--mono", "monospace"),
                    formatter: (v: number) => `$${v / 1e3}k`,
                  },
                },
                series: [
                  {
                    name: "This period",
                    type: "line",
                    data: rev.current,
                    smooth: 0.35,
                    symbol: "none",
                    itemStyle: { color: accent },
                    lineStyle: { width: 1.9, color: accent },
                    areaStyle: {
                      color: {
                        type: "linear",
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [
                          { offset: 0, color: accent + "26" },
                          { offset: 1, color: accent + "00" },
                        ],
                      },
                    },
                  },
                  {
                    name: "Previous",
                    type: "line",
                    data: rev.previous,
                    smooth: 0.35,
                    symbol: "none",
                    itemStyle: { color: faint },
                    lineStyle: { width: 1.2, color: faint, type: [4, 4] },
                  },
                ],
              };
            }}
          />
        </Panel>

        <Panel title="Traffic sources">
          <EChart
            id="srcChart"
            style={{ height: "176px" }}
            build={() => {
              const palette = ["--s1", "--s2", "--s3", "--s4", "--s5"].map(
                (v) => cssVar(v, "#ff7a1a"),
              );
              const data = TRAFFIC_SOURCES.map(([name, value], i) => ({
                name,
                value,
                itemStyle: { color: palette[i] ?? palette[0] },
              }));
              return {
                tooltip: {
                  trigger: "item",
                  valueFormatter: (value) => `${Number(value)}%`,
                },
                series: [
                  {
                    type: "pie",
                    radius: ["62%", "84%"],
                    center: ["50%", "52%"],
                    avoidLabelOverlap: false,
                    itemStyle: {
                      borderColor: cssVar("--panel", "#ffffff"),
                      borderWidth: 2,
                    },
                    label: {
                      show: true,
                      position: "center",
                      formatter: `{a|${TRAFFIC_TOTAL.toLocaleString()}}\n{b|sessions}`,
                      rich: {
                        a: {
                          fontSize: 20,
                          fontWeight: 500,
                          color: cssVar("--ink", "#14140f"),
                          fontFamily: cssVar("--mono", "monospace"),
                        },
                        b: {
                          fontSize: 11,
                          color: cssVar("--faint", "#a09a90"),
                          padding: [5, 0, 0, 0],
                        },
                      },
                    },
                    emphasis: { label: { show: true }, scale: false },
                    data,
                  },
                ],
              };
            }}
          />
          <TrafficBars />
        </Panel>
      </div>

      <div className="g2">
        <Panel title="Recent orders">
          <DataTable<Order>
            columns={orderColumns()}
            rows={filtered}
            rowKey={(r) => r.id}
            page={page}
            onPage={setPage}
            pageSize={8}
          />
        </Panel>

        <Panel title="Activity">
          <div className="feed">
            {ACTIVITY.map((ev, i) => (
              <div className="ev" key={i}>
                <span
                  className="d"
                  style={{ background: `var(--${ev.tone})` }}
                />
                <div>
                  <div className="t">{ev.title}</div>
                  <div className="m">{ev.detail}</div>
                </div>
                <span className="w" style={{ marginLeft: "auto" }}>
                  {ev.time}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function TrafficBars() {
  const ref = useRef<HTMLDivElement | null>(null);

  useLayoutEffect(() => {
    const root = ref.current;
    if (!root) return;
    const apply = () => {
      root.querySelectorAll<HTMLElement>("[data-w]").forEach((el) => {
        const w = Number(el.dataset.w || 0);
        const c = Number(el.dataset.c || 0);
        el.style.width = `${w}%`;
        el.style.background = cssVar(`--s${(c % 5) + 1}`, "#ff7a1a");
      });
    };
    if (typeof IntersectionObserver === "undefined") {
      apply();
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          apply();
          io.disconnect();
        }
      },
      { threshold: 0.3 },
    );
    io.observe(root);
    return () => io.disconnect();
  }, []);

  return (
    <div className="bars" ref={ref}>
      {TRAFFIC_SOURCES.map(([name, value], i) => (
        <div className="bar" key={name}>
          <div className="r">
            <span>{name}</span>
            <b>{value}%</b>
          </div>
          <div className="track">
            <i
              style={{ width: 0 }}
              data-w={(value / TRAFFIC_SOURCES[0][1]) * 100}
              data-c={i}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function orderColumns(): Column<Order>[] {
  const cols: Column<Order>[] = [
    { key: "id", label: "Order", sortable: true },
    { key: "customer", label: "Customer", sortable: true },
    { key: "city", label: "Market", sortable: true },
    { key: "date", label: "Date", sortable: true },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (r) => (
        <span className={`status ${statusTone[r.status] ?? ""}`}>
          {r.status}
        </span>
      ),
    },
    {
      key: "total",
      label: "Total",
      sortable: true,
      numeric: true,
      render: (r) => money(r.total),
    },
  ];
  return cols;
}
