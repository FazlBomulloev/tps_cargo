import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Table, Input, Card } from "antd";
import { getClients } from "../api/clients";
import { PageHeader, EmptyState } from "../components/ui";

export default function Clients() {
  const [data, setData] = useState<any>({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getClients({ page, per_page: perPage, q: search || undefined })
      .then((r) => {
        if (!cancelled) setData(r.data);
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
  }, [page, perPage, search]);

  return (
    <>
      <PageHeader
        title="Клиенты"
        actions={
          <Input.Search
            placeholder="Поиск по TPS / телефону / ФИО"
            style={{ maxWidth: 360 }}
            onSearch={(v) => { setSearch(v); setPage(1); }}
            allowClear
            size="large"
          />
        }
      />

      <div className="animate-fade-in-up">
        <Card styles={{ body: { padding: 0 } }} className="hover-card">
          <Table
            loading={loading}
            dataSource={data.items}
            rowKey="id"
            locale={{ emptyText: <EmptyState title="Пока нет клиентов" description="Добавьте первого клиента через Telegram-бота" /> }}
            pagination={{
              current: page,
              total: data.total,
              pageSize: perPage,
              showSizeChanger: true,
              pageSizeOptions: ["20", "50", "100"],
              onChange: (p, ps) => {
                setPage(p);
                if (ps !== perPage) setPerPage(ps);
              },
              showTotal: (total) => `Всего: ${total}`,
            }}
            columns={[
              {
                title: "TPS",
                dataIndex: "tps_code",
                width: 100,
                render: (v: string, r: any) => (
                  <Link to={`/clients/${r.id}`} style={{ fontWeight: 600, color: "#00A76F" }}>
                    {v}
                  </Link>
                ),
              },
              { title: "ФИО", dataIndex: "full_name" },
              { title: "Телефон", dataIndex: "phone", width: 160 },
              {
                title: "Регистрация",
                dataIndex: "created_at",
                width: 120,
                render: (v: string) => v?.slice(0, 10),
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
