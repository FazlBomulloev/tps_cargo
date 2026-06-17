import { useEffect, useState } from "react";
import { Card, Form, Input, InputNumber, Select, Button, message, Alert, Table, Tag, Segmented, Popconfirm, Row, Col, Grid } from "antd";
import { InboxOutlined, DeleteOutlined } from "@ant-design/icons";
import { addDushanbeParcel, addDushanbeBulk, getParcels, deleteDushanbeParcel } from "../api/parcels";
import { useAuthStore } from "../store/authStore";
import { PageHeader, TrackChip, StatusTag, MethodTag, WeightCell } from "../components/ui";
import type { ParcelStatus, DeliveryMethod } from "../types/api";
import { formatDateTimeRu } from "../utils/format";

const { useBreakpoint } = Grid;

export default function ParcelsDushanbe() {
  const [form] = Form.useForm();
  const [bulkForm] = Form.useForm();
  const [mode, setMode] = useState<"single" | "bulk">("single");
  const [loading, setLoading] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [parcels, setParcels] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [tableLoading, setTableLoading] = useState(false);
  const user = useAuthStore((s) => s.user);
  const canDelete =
    user?.role === "owner" ||
    (user?.permissions || []).includes("parcels_delete");
  const screens = useBreakpoint();
  const sticky = !!screens.lg;

  const [reloadCounter, setReloadCounter] = useState(0);

  const handleDelete = async (id: number) => {
    try {
      await deleteDushanbeParcel(id);
      message.success("Посылка удалена");
      setReloadCounter((c) => c + 1);
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка удаления");
    }
  };

  useEffect(() => {
    let cancelled = false;
    setTableLoading(true);
    getParcels({
      page,
      per_page: 20,
      q: search.trim() || undefined,
    })
      .then(({ data }) => {
        if (cancelled) return;
        setParcels(data.items || []);
        setTotal(data.total || 0);
      })
      .catch(() => {
        if (!cancelled) message.error("Не удалось загрузить посылки");
      })
      .finally(() => {
        if (!cancelled) setTableLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, search, reloadCounter]);

  const triggerReload = () => {
    if (page !== 1) setPage(1);
    else setReloadCounter((c) => c + 1);
  };

  const onFinish = async (values: any) => {
    setLoading(true);
    setResult(null);
    try {
      const { data } = await addDushanbeParcel(values);
      if (data.status === "unresolved") {
        setResult({ type: "warning", message: "TPS-код не найден, посылка сохранена как неопознанная" });
      } else {
        setResult({ type: "success", message: `Посылка добавлена. Клиент: ${data.client_name}` });
      }
      form.resetFields();
      triggerReload();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  const onBulkFinish = async (values: any) => {
    const tracks: string[] = (values.track_ids || "")
      .split(/[\n,;]+/)
      .map((t: string) => t.trim())
      .filter(Boolean);
    if (tracks.length === 0) {
      message.warning("Добавьте хотя бы один трек-код");
      return;
    }
    setBulkLoading(true);
    try {
      const { data } = await addDushanbeBulk({
        tps_code: values.tps_code || null,
        track_ids: tracks,
        weight_kg: values.weight_kg,
        delivery_method: values.delivery_method,
        volume_m3: values.volume_m3 ?? null,
        comment: values.comment || null,
        shelf: values.shelf || null,
      });
      message.success(
        `Готово: добавлено ${data.added}, неопознано ` +
          `${data.unresolved}, дубли ${data.duplicates}`
      );
      bulkForm.resetFields();
      triggerReload();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    } finally {
      setBulkLoading(false);
    }
  };

  return (
    <>
      <PageHeader title="Приёмка на складе Душанбе" />

      <Row gutter={[24, 24]} className="animate-fade-in-up">
        <Col xs={24} lg={8}>
          <div style={{ position: sticky ? "sticky" : "static", top: 24 }}>
        <Card
          className="hover-card"
          title={
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <InboxOutlined style={{ color: "#00A76F" }} />
              <span style={{ fontWeight: 600 }}>Приёмка посылки</span>
            </span>
          }
        >
          {result && (
            <div className="animate-scale-in">
              <Alert
                type={result.type}
                message={result.message}
                showIcon
                style={{ marginBottom: 20, borderRadius: 12 }}
                closable
                onClose={() => setResult(null)}
              />
            </div>
          )}
          <Segmented
            value={mode}
            onChange={(v) => setMode(v as "single" | "bulk")}
            options={[
              { label: "Одиночный", value: "single" },
              { label: "Групповой", value: "bulk" },
            ]}
            style={{ marginBottom: 20 }}
          />
          {mode === "single" && (
          <Form form={form} layout="vertical" onFinish={onFinish} size="large">
            <Form.Item name="track_id" label="Трек-код" rules={[{ required: true }]}>
              <Input placeholder="Скан или ручной ввод" autoFocus style={{ borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="tps_code" label="TPS-код клиента (необязательно)">
              <Input placeholder="TPS001" style={{ borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="weight_kg" label="Вес (кг)" rules={[{ required: true }]}>
              <InputNumber min={0.001} step={0.1} style={{ width: "100%", borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="volume_m3" label="Объём м³ (для фуры)">
              <InputNumber min={0} step={0.01} style={{ width: "100%", borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="delivery_method" label="Способ доставки" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: "avia", label: "Авиа" },
                  { value: "truck", label: "Фура" },
                ]}
              />
            </Form.Item>
            <Form.Item name="shelf" label="Полка (необязательно)">
              <Input placeholder="например, 14" style={{ borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="comment" label="Комментарий">
              <Input.TextArea rows={2} style={{ borderRadius: 12 }} />
            </Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ height: 48, borderRadius: 12, fontSize: 15, fontWeight: 600 }}
            >
              Добавить
            </Button>
          </Form>
          )}
          {mode === "bulk" && (
          <Form form={bulkForm} layout="vertical" onFinish={onBulkFinish} size="large">
            <Form.Item name="track_ids" label="Трек-коды (по одному на строку)" rules={[{ required: true }]}>
              <Input.TextArea
                rows={6}
                placeholder={"TRACK001\nTRACK002\nTRACK003"}
                autoFocus
                style={{ borderRadius: 12, fontFamily: "monospace" }}
              />
            </Form.Item>
            <Form.Item name="tps_code" label="TPS-код клиента (необязательно)">
              <Input placeholder="TPS001" style={{ borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="weight_kg" label="Вес (общий на партию, кг)" rules={[{ required: true }]}>
              <InputNumber min={0.001} step={0.1} style={{ width: "100%", borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="volume_m3" label="Объём м³ (для фуры)">
              <InputNumber min={0} step={0.01} style={{ width: "100%", borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="delivery_method" label="Способ доставки" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: "avia", label: "Авиа" },
                  { value: "truck", label: "Фура" },
                ]}
              />
            </Form.Item>
            <Form.Item name="shelf" label="Полка (одна на всю партию, необязательно)">
              <Input placeholder="например, 14" style={{ borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="comment" label="Комментарий">
              <Input.TextArea rows={2} style={{ borderRadius: 12 }} />
            </Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={bulkLoading}
              block
              style={{ height: 48, borderRadius: 12, fontSize: 15, fontWeight: 600 }}
            >
              Добавить партию
            </Button>
          </Form>
          )}
        </Card>
          </div>
        </Col>
        <Col xs={24} lg={16}>
        <Card
          title={
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontWeight: 600 }}>Последние добавленные</span>
              <Tag color="processing" style={{ borderRadius: 20, fontSize: 13 }}>
                {total}
              </Tag>
            </span>
          }
          className="hover-card"
          extra={
            <Input.Search
              placeholder="Поиск: трек, ФИО или TPS"
              allowClear
              onSearch={(v) => { setSearch(v); setPage(1); }}
              style={{ width: 260 }}
            />
          }
        >
          <Table
            dataSource={parcels}
            rowKey="id"
            size="small"
            loading={tableLoading}
            pagination={{
              current: page,
              pageSize: 20,
              total,
              onChange: (p) => setPage(p),
              showSizeChanger: false,
              showTotal: (t) => `Всего: ${t}`,
            }}
            columns={[
              {
                title: "Трек-код",
                dataIndex: "track_id",
                render: (v: string) => <TrackChip value={v} />,
              },
              {
                title: "Вес",
                dataIndex: "weight_kg",
                render: (v: number) => <WeightCell value={v} />,
                width: 100,
              },
              {
                title: "Метод",
                dataIndex: "delivery_method",
                width: 100,
                render: (v: DeliveryMethod) => <MethodTag method={v} />,
              },
              {
                title: "Статус",
                dataIndex: "status",
                width: 120,
                render: (v: ParcelStatus) => <StatusTag status={v} />,
              },
              {
                title: "Дата",
                dataIndex: "created_at",
                render: (v: string) => formatDateTimeRu(v),
              },
              ...(canDelete
                ? [
                    {
                      title: "",
                      width: 50,
                      render: (_: any, r: any) =>
                        r.status === "issued" ? null : (
                          <Popconfirm
                            title="Удалить посылку?"
                            okText="Удалить"
                            cancelText="Отмена"
                            okButtonProps={{ danger: true }}
                            onConfirm={() => handleDelete(r.id)}
                          >
                            <Button
                              size="small"
                              danger
                              type="text"
                              icon={<DeleteOutlined />}
                              aria-label="Удалить посылку"
                            />
                          </Popconfirm>
                        ),
                    },
                  ]
                : []),
            ]}
          />
        </Card>
        </Col>
      </Row>
    </>
  );
}
