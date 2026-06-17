import { useEffect, useState } from "react";
import { Table, Tag, Card, Input, DatePicker, Space } from "antd";
import type { Dayjs } from "dayjs";
import { getIssuances } from "../api/issuance";
import { PageHeader, MoneyCell, WeightCell, TrackChip } from "../components/ui";

export default function IssuanceHistory() {
  const [data, setData] = useState<any>({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);

  const load = () => {
    setLoading(true);
    const params: Record<string, unknown> = { page, per_page: 20 };
    if (search.trim()) params.search = search.trim();
    if (dateRange) {
      params.date_from = dateRange[0].startOf("day").toISOString();
      params.date_to = dateRange[1].endOf("day").toISOString();
    }
    getIssuances(params).then((r) => {
      setData(r.data);
      setLoading(false);
    });
  };

  useEffect(() => { load(); }, [page, search, dateRange]);

  return (
    <>
      <PageHeader
        title="История выдач"
        actions={
          <Space wrap>
            <Input.Search
              placeholder="Номер, TPS-код, трек-код"
              allowClear
              onSearch={(v) => { setSearch(v); setPage(1); }}
              style={{ width: 260, borderRadius: 12 }}
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
          </Space>
        }
      />

      <div className="animate-fade-in-up">
        <Card styles={{ body: { padding: 0 } }} className="hover-card">
          <Table
            loading={loading}
            dataSource={data.items}
            rowKey="id"
            pagination={{
              current: page,
              total: data.total,
              pageSize: 20,
              onChange: setPage,
              showTotal: (total) => `Всего: ${total}`,
            }}
            expandable={{
              expandedRowRender: (record: any) => (
                <Table
                  dataSource={record.items}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  columns={[
                    {
                      title: "Трек-код",
                      dataIndex: "track_id",
                      render: (v: string, r: any) =>
                        v ? <TrackChip value={v} /> : <span>{`#${r.parcel_id}`}</span>,
                    },
                    { title: "Вес", dataIndex: "weight_kg", render: (v: number) => <WeightCell value={v} /> },
                    { title: "Метод", dataIndex: "delivery_method" },
                    { title: "Тариф", dataIndex: "tariff_applied", render: (v: number) => <MoneyCell value={v} /> },
                    {
                      title: "Сумма",
                      dataIndex: "amount",
                      render: (v: number) => <MoneyCell value={v} />,
                    },
                  ]}
                />
              ),
            }}
            columns={[
              {
                title: "№ выдачи",
                dataIndex: "id",
                width: 90,
                render: (v: number) => `#${v}`,
              },
              {
                title: "Клиент",
                dataIndex: "client_name",
                render: (v: string, r: any) =>
                  v ? (
                    <span>
                      <span style={{ fontWeight: 500 }}>{v}</span>
                      <span style={{ color: "#919EAB", marginLeft: 8, fontSize: 12 }}>
                        {r.tps_code}
                      </span>
                    </span>
                  ) : (
                    <span style={{ color: "#919EAB" }}>#{r.client_id}</span>
                  ),
              },
              {
                title: "Вес",
                dataIndex: "total_weight",
                render: (v: number) => <WeightCell value={v} />,
              },
              {
                title: "Сумма",
                dataIndex: "total_amount",
                render: (v: number) => <MoneyCell value={v} />,
              },
              {
                title: "Оплата",
                dataIndex: "payment_status",
                render: (v: string) => (
                  <Tag
                    color={v === "paid" ? "success" : "error"}
                    style={{ borderRadius: 20, padding: "2px 12px" }}
                  >
                    {v === "paid" ? "Оплачено" : "Долг"}
                  </Tag>
                ),
              },
              {
                title: "Способ",
                dataIndex: "payment_method",
                render: (v: string) => v === "cash" ? "Наличные" : v === "transfer" ? "Перевод" : "—",
              },
              {
                title: "Дата",
                dataIndex: "issued_at",
                render: (v: string) => v?.slice(0, 10),
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
