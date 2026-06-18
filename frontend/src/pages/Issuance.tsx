import { useCallback, useMemo, useState } from "react";
import { Alert, Card, Input, Button, Table, Radio, message, Typography, Space, Statistic, List, InputNumber, Steps, Skeleton, Tooltip } from "antd";
import { SearchOutlined, ShoppingCartOutlined, EditOutlined } from "@ant-design/icons";
import { searchClients } from "../api/clients";
import { getParcels } from "../api/parcels";
import { getActiveTariffs } from "../api/tariffs";
import { createIssuance } from "../api/issuance";
import { PageHeader, TrackChip, MethodTag, WeightCell, MoneyCell, EmptyState } from "../components/ui";

const MAX_PARCEL_PAGES = 20;

export default function Issuance() {
  const [query, setQuery] = useState("");
  const [client, setClient] = useState<any>(null);
  const [candidates, setCandidates] = useState<any[]>([]);
  const [parcels, setParcels] = useState<any[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [tariffs, setTariffs] = useState<any[]>([]);
  const [paymentMethod, setPaymentMethod] = useState<string>("cash");
  const [paymentStatus, setPaymentStatus] = useState<string>("paid");
  const [loading, setLoading] = useState(false);
  const [comment, setComment] = useState("");
  const [customPrices, setCustomPrices] = useState<Record<number, number>>({});
  const [editingPrice, setEditingPrice] = useState<number | null>(null);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [searched, setSearched] = useState(false);

  const selectClient = async (c: any) => {
    setClient(c);
    setCandidates([]);

    const [allParcels, t] = await Promise.all([
      (async () => {
        const acc: any[] = [];
        let page = 1;
        let total = 0;
        while (true) {
          const { data } = await getParcels({
            client_id: c.id,
            status: "received_dushanbe",
            per_page: 100,
            page,
          });
          acc.push(...(data.items || []));
          total = data.total || 0;
          if (acc.length >= total) break;
          if ((data.items || []).length === 0) break;
          page += 1;
          if (page > MAX_PARCEL_PAGES) break;
        }
        if (total > acc.length) {
          message.warning(`Показаны первые ${acc.length} из ${total} посылок. Свяжитесь с админом.`);
        }
        return acc;
      })(),
      getActiveTariffs(),
    ]);
    setParcels(allParcels);
    setTariffs(t.data);
    setSelected([]);
    setCustomPrices({});
    setEditingPrice(null);
    setComment("");
  };

  const search = async () => {
    setLoadingSearch(true);
    try {
      const { data } = await searchClients(query.trim());
      setSearched(true);
      if (data.length === 0) {
        setCandidates([]);
        setClient(null);
        setParcels([]);
        setSelected([]);
        return;
      }
      if (data.length === 1) {
        await selectClient(data[0]);
      } else {
        setCandidates(data);
        setClient(null);
        setParcels([]);
        setSelected([]);
      }
    } finally {
      setLoadingSearch(false);
    }
  };

  const handleResetPrice = useCallback((id: number) => {
    setCustomPrices((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  }, []);

  const tariffByMethod = useMemo(
    () => Object.fromEntries(tariffs.map((t: any) => [t.method, t])),
    [tariffs],
  );

  const calcAmount = useCallback((p: any) => {
    const t = tariffByMethod[p.delivery_method];
    if (!t) return 0;
    if (p.delivery_method === "avia") return +(p.weight_kg * t.price_per_kg).toFixed(2);
    const byKg = p.weight_kg * t.price_per_kg;
    const byM3 = (p.volume_m3 || 0) * (t.price_per_m3 || 0);
    return +Math.max(byKg, byM3).toFixed(2);
  }, [tariffByMethod]);

  const selectedParcels = useMemo(
    () => parcels.filter((p) => selected.includes(p.id)),
    [parcels, selected],
  );
  const totalWeight = useMemo(
    () => selectedParcels.reduce((s, p) => s + +p.weight_kg, 0),
    [selectedParcels],
  );
  const totalAmount = useMemo(
    () => selectedParcels.reduce((s, p) => {
      if (p.id in customPrices) return s + customPrices[p.id];
      return s + calcAmount(p);
    }, 0),
    [selectedParcels, customPrices, calcAmount],
  );

  const requiredMethods = Array.from(
    new Set(selectedParcels.map((p) => p.delivery_method).filter(Boolean)),
  );
  const missingTariffMethods = requiredMethods.filter(
    (m) => !tariffs.some((t) => t.method === m),
  );
  const tariffsLoaded = tariffs.length > 0;
  const issueBlocked = !tariffsLoaded || missingTariffMethods.length > 0;
  const currentStep = !client ? 0 : selected.length === 0 ? 1 : 2;

  const parcelColumns = useMemo(() => [
    {
      title: "Трек",
      dataIndex: "track_id",
      render: (v: string) => <TrackChip value={v} copyable={false} />,
    },
    {
      title: "Вес",
      dataIndex: "weight_kg",
      render: (v: number) => <WeightCell value={v} />,
    },
    {
      title: "Объём",
      dataIndex: "volume_m3",
      render: (v: number) => v ? `${v} м³` : "—",
    },
    {
      title: "Метод",
      dataIndex: "delivery_method",
      render: (v: "avia" | "truck") => <MethodTag method={v} />,
    },
    {
      title: (
        <Tooltip title="Кликни по сумме, чтобы изменить">
          <span>Сумма <EditOutlined style={{ fontSize: 11, opacity: 0.6, marginLeft: 4 }} /></span>
        </Tooltip>
      ),
      render: (_: any, r: any) => {
        const isCustom = r.id in customPrices;
        const amount = isCustom ? customPrices[r.id] : calcAmount(r);
        if (editingPrice === r.id) {
          return (
            <InputNumber
              autoFocus
              size="small"
              min={0}
              step={0.01}
              precision={2}
              decimalSeparator="."
              value={amount}
              onChange={(v) => {
                if (v != null) setCustomPrices({ ...customPrices, [r.id]: Number(v) });
              }}
              onBlur={() => setEditingPrice(null)}
              onPressEnter={() => setEditingPrice(null)}
              style={{ width: 120 }}
              addonAfter="TJS"
            />
          );
        }
        return (
          <Space size={4}>
            <Tooltip title="Кликни, чтобы изменить">
              <span
                onClick={() => setEditingPrice(r.id)}
                style={{
                  fontFamily: "var(--font-mono)",
                  fontVariantNumeric: "tabular-nums",
                  cursor: "pointer",
                  padding: "2px 8px",
                  borderRadius: 4,
                  background: isCustom ? "var(--c-warning-soft)" : "transparent",
                  color: isCustom ? "var(--c-warning)" : "var(--c-text)",
                  borderBottom: isCustom ? "none" : "1px dashed var(--c-text-muted)",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                {amount.toFixed(2)} TJS
                <EditOutlined style={{ fontSize: 10, opacity: 0.5 }} />
              </span>
            </Tooltip>
            {isCustom && (
              <Tooltip title="Вернуть расчётную цену по тарифу">
                <Button size="small" type="link" onClick={() => handleResetPrice(r.id)} style={{ padding: "0 4px" }}>
                  Сбросить
                </Button>
              </Tooltip>
            )}
          </Space>
        );
      },
    },
  ], [customPrices, editingPrice, calcAmount, handleResetPrice]);

  const handleIssue = async () => {
    if (issueBlocked) {
      message.error("Тарифы не настроены — выдача недоступна");
      return;
    }
    if (!selected.length) { message.warning("Выберите посылки"); return; }
    setLoading(true);
    try {
      const cp: Record<number, number> = {};
      for (const id of selected) {
        if (id in customPrices) cp[id] = customPrices[id];
      }
      await createIssuance({
        client_id: client.id,
        parcel_ids: selected,
        payment_method: paymentStatus === "paid" ? paymentMethod : null,
        payment_status: paymentStatus,
        comment: comment.trim() || undefined,
        custom_prices: Object.keys(cp).length ? cp : undefined,
      });
      message.success(`Выдача оформлена · Итого: ${totalWeight.toFixed(1)} кг, ${totalAmount.toFixed(2)} TJS`);
      setClient(null); setParcels([]); setSelected([]);
      setQuery(""); setCandidates([]); setSearched(false);
      setComment(""); setCustomPrices({});
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHeader title="Выдача товара" />
      <Steps
        current={currentStep}
        items={[
          { title: "Поиск клиента" },
          { title: "Выбор посылок" },
          { title: "Подтверждение и выдача" },
        ]}
        style={{ marginBottom: 24 }}
      />

      <div className="stagger-children">
        <Card className="hover-card" style={{ marginBottom: 20 }}>
          <Space.Compact style={{ width: "100%", maxWidth: 500 }}>
            <Input
              placeholder="Поиск: TPS, телефон, ФИО или трек-код"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onPressEnter={search}
              prefix={<SearchOutlined style={{ color: "#919EAB" }} />}
              style={{ height: 48, borderRadius: "12px 0 0 12px", fontSize: 15 }}
            />
            <Button
              type="primary"
              onClick={search}
              loading={loadingSearch}
              style={{ height: 48, borderRadius: "0 12px 12px 0", paddingInline: 24 }}
            >
              Найти
            </Button>
          </Space.Compact>
          <Typography.Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: "block" }}>
            Поиск: TPS-код, телефон или ФИО
          </Typography.Text>
        </Card>

        {loadingSearch && (
          <Card style={{ marginBottom: 20 }}>
            <Skeleton active paragraph={{ rows: 3 }} />
          </Card>
        )}

        {!loadingSearch && searched && candidates.length === 0 && !client && (
          <Card style={{ marginBottom: 20 }}>
            <EmptyState
              title="Клиент не найден"
              description="Попробуйте ввести TPS-код, телефон или ФИО полностью"
            />
          </Card>
        )}

        {candidates.length > 1 && !client && (
          <Card
            className="hover-card animate-scale-in"
            title={
              <span style={{ fontWeight: 600 }}>
                Найдено клиентов: {candidates.length} — выберите нужного
              </span>
            }
            style={{ marginBottom: 20 }}
          >
            <List
              dataSource={candidates}
              renderItem={(c: any) => (
                <List.Item
                  style={{ cursor: "pointer", padding: "12px 16px", borderRadius: 10, transition: "background 0.2s" }}
                  onClick={() => selectClient(c)}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#F4F6F8")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <List.Item.Meta
                    avatar={
                      <div
                        style={{
                          width: 40, height: 40, borderRadius: 10,
                          background: "linear-gradient(135deg, #00A76F, #5BE49B)",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          color: "#fff", fontWeight: 700, fontSize: 16,
                        }}
                      >
                        {c.full_name?.charAt(0)?.toUpperCase()}
                      </div>
                    }
                    title={<span style={{ fontWeight: 600 }}>{c.full_name}</span>}
                    description={
                      <span style={{ color: "#637381" }}>
                        {c.tps_code} &bull; {c.phone}
                      </span>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        )}

        {client && !tariffsLoaded && (
          <Alert
            type="warning"
            showIcon
            message="Тарифы не настроены"
            description="Откройте раздел «Тарифы» и добавьте активные тарифы для авиа и фуры. Без тарифов выдача недоступна — сумма не считается."
            style={{ marginBottom: 20 }}
          />
        )}

        {client && tariffsLoaded && missingTariffMethods.length > 0 && (
          <Alert
            type="warning"
            showIcon
            message="Не настроен тариф"
            description={`Для метода ${missingTariffMethods.join(", ")} нет активного тарифа. Уберите такие посылки из выдачи или добавьте тариф.`}
            style={{ marginBottom: 20 }}
          />
        )}

        {client && (
          <Card
            className="hover-card animate-scale-in"
            title={
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    background: "linear-gradient(135deg, #00A76F, #5BE49B)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#fff",
                    fontWeight: 700,
                    fontSize: 16,
                  }}
                >
                  {client.full_name?.charAt(0)?.toUpperCase()}
                </div>
                <div>
                  <div style={{ fontWeight: 600 }}>{client.full_name}</div>
                  <div style={{ fontSize: 13, color: "#919EAB", fontWeight: 400 }}>
                    {client.tps_code} | {client.phone}
                  </div>
                </div>
              </div>
            }
          >
            <Table
              dataSource={parcels}
              rowKey="id"
              size="small"
              pagination={false}
              rowSelection={{
                selectedRowKeys: selected,
                onChange: (keys) => setSelected(keys as number[]),
              }}
              columns={parcelColumns}
            />

            <div
              style={{
                marginTop: 24,
                padding: 20,
                background: "#F4F6F8",
                borderRadius: 16,
                display: "flex",
                gap: 32,
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <Statistic
                title="Вес"
                value={totalWeight}
                formatter={() => <WeightCell value={totalWeight} />}
                valueStyle={{ fontWeight: 700, fontSize: 24 }}
              />
              <Statistic
                title="Сумма"
                value={totalAmount}
                formatter={() => <MoneyCell value={totalAmount} />}
                valueStyle={{ fontWeight: 700, fontSize: 24, color: "#00A76F" }}
              />
              <div>
                <div style={{ marginBottom: 8 }}>
                  <Radio.Group value={paymentStatus} onChange={(e) => setPaymentStatus(e.target.value)}>
                    <Radio.Button value="paid" style={{ borderRadius: "10px 0 0 10px" }}>Оплачено</Radio.Button>
                    <Radio.Button value="debt" style={{ borderRadius: "0 10px 10px 0" }}>Долг</Radio.Button>
                  </Radio.Group>
                </div>
                {paymentStatus === "paid" && (
                  <Radio.Group value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
                    <Radio.Button value="cash" style={{ borderRadius: "10px 0 0 10px" }}>Наличные</Radio.Button>
                    <Radio.Button value="transfer" style={{ borderRadius: "0 10px 10px 0" }}>Перевод</Radio.Button>
                  </Radio.Group>
                )}
              </div>
              <Button
                type="primary"
                size="large"
                onClick={handleIssue}
                loading={loading}
                disabled={issueBlocked || selected.length === 0}
                icon={<ShoppingCartOutlined />}
                style={{ borderRadius: 12, height: 48, paddingInline: 32, fontWeight: 600 }}
              >
                Выдать
              </Button>
            </div>
            <div style={{ marginTop: 16 }}>
              <Input.TextArea
                placeholder="Комментарий к выдаче"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={2}
                style={{ borderRadius: 12 }}
              />
            </div>
          </Card>
        )}
      </div>
    </>
  );
}
