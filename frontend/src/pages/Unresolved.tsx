import { useEffect, useState } from "react";
import { Table, Button, Input, Modal, message, Tag, Card, Space, Popconfirm } from "antd";
import { WarningOutlined, LinkOutlined, DeleteOutlined } from "@ant-design/icons";
import { getUnresolved, resolveParcel, deleteUnresolved } from "../api/unresolved";
import type { DeliveryMethod } from "../types/api";
import { PageHeader, TrackChip, MethodTag, WeightCell, EmptyState } from "../components/ui";

export default function Unresolved() {
  const [items, setItems] = useState<any[]>([]);
  const [resolveId, setResolveId] = useState<number | null>(null);
  const [tpsCode, setTpsCode] = useState("");
  const [search, setSearch] = useState("");

  const load = (s: string = search) =>
    getUnresolved(s.trim() || undefined).then((r) => setItems(r.data));
  useEffect(() => { load(""); }, []);

  const handleResolve = async () => {
    if (!tpsCode.trim()) return;
    try {
      await resolveParcel(resolveId!, tpsCode.trim());
      message.success("Посылка привязана к клиенту");
      setResolveId(null); setTpsCode(""); load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    }
  };

  const handleDelete = async (id: number) => {
    await deleteUnresolved(id);
    message.success("Удалено");
    load();
  };

  return (
    <>
      <PageHeader
        title="Неопознанные посылки"
        actions={
          items.length > 0 && (
            <Tag
              color="error"
              style={{
                borderRadius: 20,
                padding: "4px 16px",
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              <WarningOutlined /> {items.length} шт.
            </Tag>
          )
        }
      />

      <div className="animate-fade-in-up">
        <Card
          styles={{ body: { padding: 0 } }}
          className="hover-card"
          title={
            <Input.Search
              placeholder="Поиск: трек-код, TPS или комментарий"
              allowClear
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onSearch={(v) => { setSearch(v); load(v); }}
              style={{ maxWidth: 400 }}
            />
          }
        >
          <Table
            dataSource={items}
            rowKey="id"
            locale={{ emptyText: <EmptyState title="Все треки опознаны" description="Нет посылок, ожидающих привязки к клиенту" /> }}
            columns={[
              {
                title: "Трек",
                dataIndex: "track_id",
                render: (v: string) => <TrackChip value={v} />,
              },
              {
                title: "TPS (введённый)",
                dataIndex: "raw_tps_code",
                render: (v: string) => (
                  <Tag color="error" style={{ borderRadius: 20, padding: "2px 12px" }}>{v}</Tag>
                ),
              },
              {
                title: "Вес",
                dataIndex: "weight_kg",
                render: (v: number) => (v ? <WeightCell value={v} /> : "—"),
              },
              {
                title: "Метод",
                dataIndex: "delivery_method",
                render: (v: DeliveryMethod | null) => (v ? <MethodTag method={v} /> : "—"),
              },
              {
                title: "Полка",
                dataIndex: "shelf",
                width: 80,
                render: (v: string | null) =>
                  v ? (
                    <Tag color="default" style={{ borderRadius: 8, fontWeight: 600 }}>{v}</Tag>
                  ) : (
                    <span style={{ color: "var(--c-text-muted)" }}>—</span>
                  ),
              },
              {
                title: "Комментарий",
                dataIndex: "comment",
                ellipsis: { showTitle: true },
                render: (v: string | null) =>
                  v ? <span>{v}</span> : <span style={{ color: "var(--c-text-muted)" }}>—</span>,
              },
              { title: "Дата", dataIndex: "created_at", render: (v: string) => v?.slice(0, 10) },
              {
                title: "Действия",
                width: 200,
                render: (_: any, r: any) => (
                  <Space>
                    <Button
                      size="small"
                      type="primary"
                      icon={<LinkOutlined />}
                      onClick={() => setResolveId(r.id)}
                      style={{ borderRadius: 8 }}
                    >
                      Привязать
                    </Button>
                    <Popconfirm
                      title="Удалить неопознанную посылку?"
                      description="Действие необратимо."
                      okText="Удалить"
                      cancelText="Отмена"
                      okButtonProps={{ danger: true }}
                      onConfirm={() => handleDelete(r.id)}
                    >
                      <Button
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        aria-label="Удалить неопознанную посылку"
                        style={{ borderRadius: 8 }}
                      />
                    </Popconfirm>
                  </Space>
                ),
              },
            ]}
          />
        </Card>
      </div>

      <Modal
        title="Привязать к клиенту"
        open={resolveId !== null}
        onOk={handleResolve}
        onCancel={() => setResolveId(null)}
        okText="Привязать"
        cancelText="Отмена"
      >
        <Input
          placeholder="Правильный TPS-код"
          value={tpsCode}
          onChange={(e) => setTpsCode(e.target.value)}
          style={{ borderRadius: 12, height: 44 }}
          size="large"
        />
      </Modal>
    </>
  );
}
