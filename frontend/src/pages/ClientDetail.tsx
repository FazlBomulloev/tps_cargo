import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Descriptions, Table, Button, Space, Skeleton } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { getClient } from "../api/clients";
import { getParcels } from "../api/parcels";
import type { ParcelStatus, DeliveryMethod } from "../types/api";
import { PageHeader, StatusTag, MethodTag, TrackChip, MoneyCell, WeightCell, EmptyState } from "../components/ui";

export default function ClientDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [client, setClient] = useState<any>(null);
  const [parcels, setParcels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { data: c } = await getClient(+id!);
      setClient(c);
      const { data: p } = await getParcels({ client_id: c.id, per_page: 100 });
      setParcels(p.items || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (id) load(); }, [id]);

  if (loading) return <Skeleton active />;
  if (!client) return <EmptyState title="Клиент не найден" />;

  return (
    <>
      <PageHeader
        title={`Клиент ${client.tps_code}`}
        actions={
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(-1)}
            aria-label="Назад"
            style={{ borderRadius: 10 }}
          />
        }
      />

      <div className="stagger-children">
        <Card className="hover-card" style={{ marginBottom: 20 }}>
          <Descriptions
            bordered
            column={{ xs: 1, sm: 2 }}
            labelStyle={{ fontWeight: 600, color: "#637381", background: "#F9FAFB" }}
          >
            <Descriptions.Item label="TPS-код">
              <span style={{ fontWeight: 600, color: "#00A76F" }}>{client.tps_code}</span>
            </Descriptions.Item>
            <Descriptions.Item label="ФИО">{client.full_name}</Descriptions.Item>
            <Descriptions.Item label="Телефон">{client.phone}</Descriptions.Item>
            <Descriptions.Item label="Telegram ID">{client.telegram_id}</Descriptions.Item>
            <Descriptions.Item label="Язык">{client.lang}</Descriptions.Item>
            <Descriptions.Item label="Регистрация">{client.created_at?.slice(0, 10)}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card
          title={<span style={{ fontWeight: 600 }}>Посылки</span>}
          className="hover-card"
        >
          <Table
            dataSource={parcels}
            rowKey="id"
            size="small"
            columns={[
              {
                title: "Трек",
                dataIndex: "track_id",
                render: (v: string) => <TrackChip value={v} />,
              },
              {
                title: "Статус",
                dataIndex: "status",
                render: (v: ParcelStatus) => <StatusTag status={v} />,
              },
              { title: "Вес", dataIndex: "weight_kg", render: (v: number) => <WeightCell value={v} /> },
              {
                title: "Метод",
                dataIndex: "delivery_method",
                render: (v: DeliveryMethod) => <MethodTag method={v} />,
              },
              {
                title: "Сумма",
                dataIndex: "amount_due",
                render: (v: number) => (v ? <MoneyCell value={v} /> : "—"),
              },
              { title: "Дата", dataIndex: "created_at", render: (v: string) => v?.slice(0, 10) },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
