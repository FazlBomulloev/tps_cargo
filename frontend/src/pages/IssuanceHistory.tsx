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
  const [sortBy, setSortBy] = useState<"id" | "issued_at" | "total_amount" | "total_weight">("issued_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const load = () => {
    setLoading(true);
    const params: Record<string, unknown> = {
      page,
      per_page: 20,
      sort_by: sortBy,
      sort_order: sortOrder,
    };
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

  useEffect(() => { load(); }, [page, search, dateRange, sortBy, sortOrder]);

  const handleTableChange = (_pagination: any, _filters: any, sorter: any) => {
    if (sorter && sorter.field) {
      const next = sorter.order === "ascend" ? "asc" : "desc";
      const field = sorter.field as typeof sortBy;
      if (["id", "issued_at", "total_amount", "total_weight"].includes(field)) {
        setSortBy(field);
        setSortOrder(next);
      }
    } else {
      // sorter clear
      setSortBy("issued_at");
      setSortOrder("desc");
    }
  };

  const sortOrderFor = (field: typeof sortBy) =>
    sortBy === field ? (sortOrder === "asc" ? "ascend" : "descend") : null;

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
            onChange={handleTableChange}
            pagination={{
              current: page,
              total: data.total,
              pageSize: 20,
              onChange: setPage,
              showTotal: (total) => `Всего: ${total}`,
            }}
            expandable={{
              expandedRowRender: (record: any) => (
                <div style={{ padding: "8px 0" }}>
                  {record.comment && (
                    <div style={{
                      marginBottom: 12,
                      padding: "10px 14px",
                      background: "#FFFBEF",
                      borderLeft: "3px solid #FFAB00",
                      borderRadius: 4,
                      fontSize: 13,
                      whiteSpace: "pre-wrap",
                    }}>
                      <span style={{ fontWeight: 600, color: "#637381", marginRight: 6 }}>Комментарий:</span>
                      {record.comment}
                    </div>
                  )}
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
                </div>
              ),
            }}
            columns={[
              {
                title: "№ выдачи",
                dataIndex: "id",
                key: "id",
                width: 110,
                sorter: true,
                sortOrder: sortOrderFor("id"),
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
                key: "total_weight",
                sorter: true,
                sortOrder: sortOrderFor("total_weight"),
                render: (v: number) => <WeightCell value={v} />,
              },
              {
                title: "Сумма",
                dataIndex: "total_amount",
                key: "total_amount",
                sorter: true,
                sortOrder: sortOrderFor("total_amount"),
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
                key: "issued_at",
                sorter: true,
                sortOrder: sortOrderFor("issued_at"),
                render: (v: string) => v?.slice(0, 10),
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
