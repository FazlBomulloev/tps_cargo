import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Table, Select, Space, Card, DatePicker, Statistic, Button, Popconfirm, message, Input } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import type { Dayjs } from "dayjs";
import { getAllParcels, deleteDushanbeParcel, deleteChinaParcel } from "../api/parcels";
import { useAuthStore } from "../store/authStore";
import type { ParcelStatus, DeliveryMethod } from "../types/api";
import { PageHeader, StatusTag, MethodTag, TrackChip, WeightCell } from "../components/ui";
import { formatDateTimeRu } from "../utils/format";

const statusLabels: Record<string, string> = {
  in_china: "В Китае",
  received_dushanbe: "В Душанбе",
  issued: "Получена",
  unresolved: "Неопознанные",
  dushanbe: "В Душанбе (принятые + неопознанные)",
};
// Значения для выпадающего фильтра (без комбинированного
// «dushanbe» — он приходит ссылкой с дашборда).
const FILTER_OPTIONS = [
  "in_china",
  "received_dushanbe",
  "issued",
  "unresolved",
];

export default function ParcelsList() {
  const [data, setData] = useState<any>({ items: [], total: 0 });
  const [searchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [status, setStatus] = useState<string | undefined>(
    searchParams.get("status") ?? undefined,
  );
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const user = useAuthStore((s) => s.user);
  const canDelete =
    user?.role === "owner" ||
    (user?.permissions || []).includes("parcels_delete");

  const [reloadCounter, setReloadCounter] = useState(0);

  const handleDelete = async (r: any) => {
    try {
      if (r.status === "in_china") {
        await deleteChinaParcel(r.id);
      } else {
        await deleteDushanbeParcel(r.id);
      }
      message.success("Посылка удалена");
      setReloadCounter((c) => c + 1);
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка удаления");
    }
  };

  useEffect(() => {
    let cancelled = false;
    const params: Record<string, unknown> = { page, per_page: perPage, status };
    if (search.trim()) params.q = search.trim();
    if (dateRange) {
      params.date_from = dateRange[0].startOf("day").toISOString();
      params.date_to = dateRange[1].endOf("day").toISOString();
    }
    setLoading(true);
    getAllParcels(params)
      .then(({ data: d }) => {
        if (!cancelled) setData(d);
      })
      .catch(() => {
        if (!cancelled) setData({ items: [], total: 0 });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, perPage, status, dateRange, search, reloadCounter]);

  return (
    <>
      <PageHeader
        title="Все посылки"
        actions={
          <Space wrap>
            <Input.Search
              placeholder="Поиск: ФИО, TPS или трек"
              allowClear
              onSearch={(v) => { setSearch(v); setPage(1); }}
              style={{ width: 260 }}
            />
            <Select
              allowClear
              placeholder="Статус"
              style={{ width: 180 }}
              value={status}
              onChange={(v) => { setStatus(v); setPage(1); }}
              options={[
                ...FILTER_OPTIONS,
                ...(status === "dushanbe" ? ["dushanbe"] : []),
              ].map((k) => ({ value: k, label: statusLabels[k] }))}
            />
            <DatePicker.RangePicker
              value={dateRange}
              onChange={(dates) => {
                setDateRange(dates as [Dayjs, Dayjs] | null);
                setPage(1);
              }}
              format="DD.MM.YYYY"
              placeholder={["Дата от", "Дата до"]}
              style={{ borderRadius: 12 }}
            />
            <Select
              value={perPage}
              onChange={(v) => { setPerPage(v); setPage(1); }}
              style={{ width: 110 }}
              options={[
                { value: 20, label: "20 / стр" },
                { value: 50, label: "50 / стр" },
                { value: 100, label: "100 / стр" },
                { value: 200, label: "200 / стр" },
              ]}
            />
          </Space>
        }
      />

      <div className="animate-fade-in-up">
        <Card styles={{ body: { padding: 0 } }} className="hover-card">
          <Table
            loading={loading}
            dataSource={data.items}
            rowKey={(r) => `${r.status === "in_china" ? "c" : "d"}_${r.id}`}
            virtual={perPage >= 100}
            scroll={perPage >= 100 ? { y: 600, x: "max-content" } : undefined}
            pagination={{
              current: page,
              total: data.total,
              pageSize: perPage,
              onChange: setPage,
              showTotal: (total) => `Всего: ${total}`,
            }}
            columns={[
              {
                title: "Трек",
                dataIndex: "track_id",
                render: (v: string, r: any) =>
                  r.status !== "in_china" ? (
                    <Link to={`/parcels/${r.id}`}>
                      <TrackChip value={v} copyable={false} />
                    </Link>
                  ) : (
                    <TrackChip value={v} />
                  ),
              },
              {
                title: "Клиент",
                dataIndex: "client_name",
                render: (v: string, r: any) =>
                  v ? (
                    <span>
                      <span style={{ fontWeight: 500 }}>{v}</span>
                      <span style={{ color: "#919EAB", marginLeft: 8, fontSize: 12 }}>{r.tps_code}</span>
                    </span>
                  ) : (
                    <span style={{ color: "#919EAB" }}>—</span>
                  ),
              },
              {
                title: "Статус",
                dataIndex: "status",
                width: 140,
                render: (v: ParcelStatus) => <StatusTag status={v} />,
              },
              {
                title: "Вес",
                dataIndex: "weight_kg",
                width: 90,
                render: (v: number | null) =>
                  v != null ? <WeightCell value={v} /> : <span style={{ color: "#919EAB" }}>—</span>,
              },
              {
                title: "Метод",
                dataIndex: "delivery_method",
                width: 90,
                render: (v: DeliveryMethod | null) =>
                  v ? <MethodTag method={v} /> : <span style={{ color: "#919EAB" }}>—</span>,
              },
              {
                title: "Дата",
                dataIndex: "created_at",
                width: 160,
                render: (v: string) => formatDateTimeRu(v),
              },
              ...(canDelete
                ? [
                    {
                      title: "",
                      width: 60,
                      render: (_: any, r: any) =>
                        r.status === "in_china" ||
                        r.status === "received_dushanbe" ? (
                          <Popconfirm
                            title="Удалить посылку?"
                            description="Посылку можно будет восстановить только вручную."
                            okText="Удалить"
                            cancelText="Отмена"
                            okButtonProps={{ danger: true }}
                            onConfirm={() => handleDelete(r)}
                          >
                            <Button
                              size="small"
                              danger
                              type="text"
                              icon={<DeleteOutlined />}
                              aria-label="Удалить посылку"
                            />
                          </Popconfirm>
                        ) : null,
                    },
                  ]
                : []),
            ]}
          />
          {(data.total_weight != null || data.total_amount != null) && (
            <div
              style={{
                padding: "16px 24px",
                borderTop: "1px solid #F4F6F8",
                display: "flex",
                gap: 32,
              }}
            >
              <Statistic
                title="Итого вес"
                value={data.total_weight ?? 0}
                precision={2}
                suffix="кг"
                valueStyle={{ fontWeight: 700, fontSize: 18 }}
              />
              <Statistic
                title="Итого сумма"
                value={data.total_amount ?? 0}
                suffix="TJS"
                valueStyle={{ fontWeight: 700, fontSize: 18, color: "#00A76F" }}
              />
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
