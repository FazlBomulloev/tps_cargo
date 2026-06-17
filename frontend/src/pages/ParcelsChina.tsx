import { useEffect, useRef, useState } from "react";
import { Card, Input, Button, message, Typography, Divider, Space, Tag, Table, Popconfirm } from "antd";
import { ScanOutlined, CloudUploadOutlined, CheckCircleOutlined, DeleteOutlined } from "@ant-design/icons";
import { addChinaParcel, addChinaBulk, getChinaParcels, deleteChinaParcel } from "../api/parcels";
import { useAuthStore } from "../store/authStore";
import { TrackChip, PageHeader } from "../components/ui";
import { formatDateTimeRu } from "../utils/format";

const { TextArea } = Input;

export default function ParcelsChina() {
  const [singleTrack, setSingleTrack] = useState("");
  const [bulkText, setBulkText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [parcels, setParcels] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [tableLoading, setTableLoading] = useState(false);
  const inputRef = useRef<any>(null);
  const user = useAuthStore((s) => s.user);
  const canDelete =
    user?.role === "owner" ||
    (user?.permissions || []).includes("parcels_delete");

  const [reloadCounter, setReloadCounter] = useState(0);

  const handleDelete = async (id: number) => {
    try {
      await deleteChinaParcel(id);
      message.success("Посылка удалена");
      setReloadCounter((c) => c + 1);
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка удаления");
    }
  };

  useEffect(() => {
    let cancelled = false;
    setTableLoading(true);
    getChinaParcels({
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

  const handleSingle = async () => {
    if (!singleTrack.trim()) return;
    setLoading(true);
    try {
      await addChinaParcel(singleTrack.trim());
      message.success(`Трек ${singleTrack.trim().toUpperCase()} добавлен`);
      setSingleTrack("");
      inputRef.current?.focus();
      triggerReload();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  const handleBulk = async () => {
    const tracks = bulkText.split("\n").map((t) => t.trim()).filter(Boolean);
    if (!tracks.length) return;
    setLoading(true);
    try {
      const { data } = await addChinaBulk(tracks);
      setResult(data);
      message.success(`Добавлено: ${data.added} из ${data.total}`);
      setBulkText("");
      triggerReload();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") { e.preventDefault(); handleSingle(); }
  };

  return (
    <>
      <PageHeader title="Склад Китай" />

      <div className="stagger-children">
        <Card
          title={
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <ScanOutlined style={{ color: "#00A76F" }} />
              <span style={{ fontWeight: 600 }}>Одиночный скан</span>
            </span>
          }
          className="hover-card"
          style={{ marginBottom: 20 }}
        >
          <Space.Compact style={{ width: "100%" }}>
            <Input
              ref={inputRef}
              placeholder="Трек-код (скан или ввод)"
              value={singleTrack}
              onChange={(e) => setSingleTrack(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
              style={{ height: 48, fontSize: 15, borderRadius: "12px 0 0 12px" }}
            />
            <Button
              type="primary"
              loading={loading}
              onClick={handleSingle}
              icon={<CheckCircleOutlined />}
              style={{ height: 48, borderRadius: "0 12px 12px 0", paddingInline: 24 }}
            >
              Добавить
            </Button>
          </Space.Compact>
        </Card>

        <Card
          title={
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <CloudUploadOutlined style={{ color: "#00A76F" }} />
              <span style={{ fontWeight: 600 }}>Массовый ввод</span>
            </span>
          }
          className="hover-card"
        >
          <TextArea
            rows={8}
            placeholder="Каждая строка — отдельный трек-код"
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
            style={{ borderRadius: 12, fontSize: 14, fontFamily: "monospace" }}
          />
          <Typography.Text type="secondary" style={{ fontSize: 12, display: "block", marginTop: 6 }}>
            Один трек на строку, A-Z 0-9, без пробелов
          </Typography.Text>
          <Button
            type="primary"
            style={{ marginTop: 16, height: 44, borderRadius: 12 }}
            loading={loading}
            onClick={handleBulk}
            icon={<CloudUploadOutlined />}
          >
            Добавить все
          </Button>

          {result && (
            <div className="animate-fade-in-up" style={{ marginTop: 20 }}>
              <Divider style={{ margin: "16px 0" }} />
              <Space size={8}>
                <Tag
                  color="processing"
                  style={{ fontSize: 13, padding: "4px 14px", borderRadius: 20 }}
                >
                  Всего: {result.total}
                </Tag>
                <Tag
                  color="success"
                  style={{ fontSize: 13, padding: "4px 14px", borderRadius: 20 }}
                >
                  Добавлено: {result.added}
                </Tag>
                <Tag
                  color="warning"
                  style={{ fontSize: 13, padding: "4px 14px", borderRadius: 20 }}
                >
                  Дубли: {result.duplicates}
                </Tag>
              </Space>
              {result.duplicate_list?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                    Дубликаты: {result.duplicate_list.join(", ")}
                  </Typography.Text>
                </div>
              )}
            </div>
          )}
        </Card>

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
          style={{ marginTop: 20 }}
          extra={
            <Input.Search
              placeholder="Поиск по трек-коду"
              allowClear
              onSearch={(v) => { setSearch(v); setPage(1); }}
              style={{ width: 240 }}
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
                title: "Дата",
                dataIndex: "created_at",
                render: (v: string) => formatDateTimeRu(v),
              },
              ...(canDelete
                ? [
                    {
                      title: "",
                      width: 50,
                      render: (_: any, r: any) => (
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
      </div>
    </>
  );
}
