import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Alert, Button, Card, Col, DatePicker, Popover, Row, Select, Table } from "antd";
import {
  SendOutlined,
  CarOutlined,
  InboxOutlined,
  WalletOutlined,
  UserAddOutlined,
  DatabaseOutlined,
  ExclamationCircleFilled,
  ClockCircleOutlined,
} from "@ant-design/icons";
import {
  getOverview,
  getTopClients,
  getStuckParcels,
  getParcelsByDay,
  getRevenue,
} from "../api/stats";
import dayjs from "dayjs";
import type { ReactNode } from "react";
import { StatCard, MoneyCell, WeightCell, PageHeader } from "../components/ui";
import { LazyChartFallback } from "../components/LazyChartFallback";

const Line = lazy(() =>
  import("@ant-design/charts").then((m) => ({ default: m.Line }))
);
const Column = lazy(() =>
  import("@ant-design/charts").then((m) => ({ default: m.Column }))
);

const { RangePicker } = DatePicker;

const fmtMoney = (n: number) =>
  `${n.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} TJS`;
const fmtKg = (n: number) =>
  n >= 1000 ? `${(n / 1000).toFixed(2)} т` : `${n.toFixed(1)} кг`;

function methodBreakdown(
  data: Record<string, number> | undefined,
  fmt: (n: number) => string,
) {
  return (
    <div style={{ minWidth: 140 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <SendOutlined style={{ fontSize: 12, color: "var(--c-text-muted)" }} />
          Авиа
        </span>
        <b>{fmt(data?.avia ?? 0)}</b>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, marginTop: 4 }}>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <CarOutlined style={{ fontSize: 12, color: "var(--c-text-muted)" }} />
          Фура
        </span>
        <b>{fmt(data?.truck ?? 0)}</b>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [period, setPeriod] = useState("30d");
  const [customRange, setCustomRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [overview, setOverview] = useState<any>({});
  const [topClients, setTopClients] = useState<any[]>([]);
  const [stuck, setStuck] = useState<any[]>([]);
  const [parcelsByDay, setParcelsByDay] = useState<any[]>([]);
  const [revenue, setRevenue] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [reloadCounter, setReloadCounter] = useState(0);

  const retry = useCallback(() => {
    setError(null);
    setReloadCounter((c) => c + 1);
  }, []);

  useEffect(() => {
    if (period === "custom" && !customRange) return;
    const fromDate = period === "custom" && customRange ? customRange[0].format("YYYY-MM-DD") : undefined;
    const toDate = period === "custom" && customRange ? customRange[1].format("YYYY-MM-DD") : undefined;
    let cancelled = false;
    setError(null);
    Promise.all([
      getOverview(period, fromDate, toDate),
      getTopClients(period, fromDate, toDate),
      getStuckParcels(period, fromDate, toDate),
      getParcelsByDay(period, fromDate, toDate),
      getRevenue(period, fromDate, toDate),
    ])
      .then(([o, tc, st, pbd, rv]) => {
        if (cancelled) return;
        setOverview(o.data);
        setTopClients(tc.data);
        setStuck(st.data);
        setParcelsByDay(Array.isArray(pbd.data) ? pbd.data : []);
        setRevenue(Array.isArray(rv.data) ? rv.data : []);
      })
      .catch((err) => {
        if (cancelled || axios.isCancel(err)) return;
        setError("Не удалось загрузить статистику");
      });
    return () => {
      cancelled = true;
    };
  }, [period, customRange, reloadCounter]);

  const stats: Array<{
    title: string;
    value: ReactNode;
    caption?: string;
    icon: ReactNode;
    accent: "primary" | "warning" | "error" | "info" | "neutral";
    link?: string;
    popoverTitle?: string;
    popover?: ReactNode;
  }> = useMemo(() => [
    {
      title: "Посылок в Китае",
      value: overview.china_count ?? 0,
      icon: <SendOutlined />,
      accent: "primary",
      link: "/parcels?status=in_china",
    },
    {
      title: "Активные в Душанбе",
      value: overview.dushanbe_count ?? 0,
      icon: <InboxOutlined />,
      accent: "neutral",
      link: "/parcels?status=dushanbe",
    },
    {
      title: "Добавлено за период",
      value: overview.added_count ?? 0,
      icon: <InboxOutlined />,
      accent: "neutral",
      popoverTitle: "По складам",
      popover: (
        <div style={{ minWidth: 160 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center" }}>
            <span style={{
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              fontWeight: 600,
              background: "var(--c-primary-soft)",
              padding: "1px 6px",
              borderRadius: 4,
            }}>CN</span>
            <b>{overview.china_added ?? 0}</b>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 16, marginTop: 4, alignItems: "center" }}>
            <span style={{
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              fontWeight: 600,
              background: "var(--c-primary-soft)",
              padding: "1px 6px",
              borderRadius: 4,
            }}>TJ</span>
            <b>{overview.dushanbe_added ?? 0}</b>
          </div>
        </div>
      ),
    },
    {
      title: "Выручка",
      value: <MoneyCell value={overview.revenue ?? 0} />,
      icon: <WalletOutlined />,
      accent: "primary",
      popover: methodBreakdown(overview.revenue_by_method, fmtMoney),
    },
    {
      title: "Общий вес",
      value: <WeightCell value={overview.total_weight ?? 0} />,
      icon: <DatabaseOutlined />,
      accent: "neutral",
      popover: methodBreakdown(overview.weight_by_method, fmtKg),
    },
    {
      title: "Новых клиентов",
      value: overview.new_clients ?? 0,
      icon: <UserAddOutlined />,
      accent: "neutral",
      link: "/clients",
    },
  ], [overview]);

  const lineConfig = useMemo(() => ({
    data: parcelsByDay,
    xField: "date",
    yField: "count",
    smooth: true,
    height: 300,
    color: "#00A76F",
    areaStyle: {
      fill: "l(270) 0:rgba(0,167,111,0.01) 1:rgba(0,167,111,0.15)",
    },
    line: {
      style: { lineWidth: 3 },
    },
    point: {
      size: 0,
      style: { fill: "#00A76F" },
    },
    xAxis: {
      label: {
        formatter: (v: string) => {
          const d = new Date(v);
          return `${d.getDate()}.${String(d.getMonth() + 1).padStart(2, "0")}`;
        },
      },
    },
    tooltip: {
      formatter: (datum: any) => ({
        name: "Посылки",
        value: datum.count,
      }),
    },
  }), [parcelsByDay]);

  const columnConfig = useMemo(() => ({
    data: revenue,
    xField: "period",
    yField: "amount",
    height: 300,
    color: "#00A76F",
    columnStyle: {
      radius: [6, 6, 0, 0],
    },
    tooltip: {
      formatter: (datum: any) => ({
        name: "Выручка",
        value: `${datum.amount} TJS`,
      }),
    },
  }), [revenue]);

  return (
    <>
      <PageHeader
        title="Дашборд"
        actions={
          <>
            <Select
              value={period}
              onChange={(v) => { setPeriod(v); if (v !== "custom") setCustomRange(null); }}
              style={{ width: 180 }}
              options={[
                { value: "today", label: "Сегодня" },
                { value: "7d", label: "7 дней" },
                { value: "30d", label: "30 дней" },
                { value: "90d", label: "90 дней" },
                { value: "all", label: "За всё время" },
                { value: "custom", label: "Свой диапазон" },
              ]}
            />
            {period === "custom" && (
              <RangePicker
                value={customRange}
                onChange={(dates) => setCustomRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
                format="DD.MM.YYYY"
                style={{ borderRadius: 8 }}
              />
            )}
          </>
        }
      />

      {error && (
        <Alert
          type="error"
          message={error}
          closable
          onClose={() => setError(null)}
          action={
            <Button size="small" type="primary" onClick={retry}>
              Повторить
            </Button>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={[20, 20]} className="stagger-children">
        {stats.map((s, i) => {
          const card = (
            <StatCard
              title={s.title}
              value={s.value}
              caption={s.caption}
              icon={s.icon}
              accent={s.accent}
              href={s.link}
            />
          );
          let wrapped: ReactNode = card;
          if (s.link) {
            wrapped = (
              <Link
                to={s.link}
                aria-label={`Перейти к разделу: ${s.title}. Значение: ${typeof s.value === "number" ? s.value : ""}`}
                style={{ textDecoration: "none", color: "inherit", display: "block", height: "100%" }}
              >
                {card}
              </Link>
            );
          }
          if (s.popover) {
            wrapped = (
              <Popover content={s.popover} title={s.popoverTitle} trigger="hover" placement="bottom">
                <div role="button" tabIndex={0}>{wrapped}</div>
              </Popover>
            );
          }
          return (
            <Col xs={24} sm={12} md={8} xl={8} key={i}>
              {wrapped}
            </Col>
          );
        })}
      </Row>

      <Row gutter={[20, 20]} style={{ marginTop: 20 }}>
        <Col xs={24} lg={parcelsByDay.length > 0 ? 14 : 24}>
          {parcelsByDay.length > 0 && (
            <Card
              title={
                <span style={{ fontWeight: 600, fontSize: 16 }}>
                  Посылки по дням
                </span>
              }
              className="animate-fade-in-up hover-card"
            >
              <Suspense fallback={<LazyChartFallback height={300} />}>
                <Line {...(lineConfig as any)} />
              </Suspense>
            </Card>
          )}
          {parcelsByDay.length === 0 && revenue.length === 0 && null}
        </Col>
        {revenue.length > 0 && (
          <Col xs={24} lg={parcelsByDay.length > 0 ? 10 : 24}>
            <Card
              title={
                <span style={{ fontWeight: 600, fontSize: 16 }}>
                  Выручка по неделям
                </span>
              }
              className="animate-fade-in-up hover-card"
            >
              <Suspense fallback={<LazyChartFallback height={300} />}>
                <Column {...(columnConfig as any)} />
              </Suspense>
            </Card>
          </Col>
        )}
      </Row>

      <Row gutter={[20, 20]} style={{ marginTop: 20 }}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <span style={{ fontWeight: 600, fontSize: 16 }}>
                Топ-10 клиентов
              </span>
            }
            className="animate-fade-in-up hover-card"
          >
            <Table
              dataSource={topClients}
              rowKey="client_id"
              size="small"
              pagination={false}
              columns={[
                {
                  title: "TPS",
                  dataIndex: "tps_code",
                  width: 100,
                  render: (v: string) => (
                    <span style={{ fontWeight: 600, color: "#00A76F" }}>
                      {v}
                    </span>
                  ),
                },
                { title: "Имя", dataIndex: "full_name" },
                {
                  title: "Сумма",
                  dataIndex: "total_amount",
                  render: (v: number) => <MoneyCell value={v ?? 0} />,
                },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            title={
              <span style={{ fontWeight: 600, fontSize: 16 }}>
                Зависшие посылки (14+ дней)
              </span>
            }
            className="animate-fade-in-up hover-card"
            extra={
              stuck.length > 0 && (
                <span
                  style={{
                    background: "#FFF2E8",
                    color: "#E65100",
                    padding: "4px 12px",
                    borderRadius: 20,
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                >
                  {stuck.length} шт.
                </span>
              )
            }
          >
            <Table
              dataSource={stuck}
              rowKey="parcel_id"
              size="small"
              pagination={false}
              columns={[
                {
                  title: "Трек",
                  dataIndex: "track_id",
                  width: 140,
                  render: (v: string) => (
                    <span style={{ fontFamily: "monospace", fontSize: 13 }}>
                      {v}
                    </span>
                  ),
                },
                { title: "Клиент", dataIndex: "full_name" },
                {
                  title: "Дней",
                  dataIndex: "waiting_days",
                  width: 70,
                  render: (v: number) => (
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                        color: v > 21 ? "var(--c-error)" : "var(--c-warning)",
                        fontWeight: 600,
                      }}
                    >
                      {v > 21 ? <ExclamationCircleFilled /> : <ClockCircleOutlined />}
                      {v}
                    </span>
                  ),
                },
                { title: "Телефон", dataIndex: "phone" },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </>
  );
}
