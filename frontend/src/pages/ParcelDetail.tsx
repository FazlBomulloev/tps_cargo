import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Descriptions, Tag, Select, Button, message, Skeleton, Alert } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import api from "../api/client";
import { getParcel, updateParcelStatus } from "../api/parcels";
import type { ParcelStatus } from "../types/api";
import { PageHeader, StatusTag, MethodTag, TrackChip, MoneyCell, WeightCell, EmptyState } from "../components/ui";

const statusLabels: Record<string, string> = {
  received_dushanbe: "В Душанбе",
};

interface IssuanceInfo {
  order_id: number;
  comment: string | null;
  issued_at: string;
  payment_status: string;
  payment_method: string | null;
  total_amount: number;
  custom_price: number | null;
  amount: number;
}

export default function ParcelDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [parcel, setParcel] = useState<any>(null);
  const [newStatus, setNewStatus] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [issuance, setIssuance] = useState<IssuanceInfo | null>(null);

  useEffect(() => {
    if (id) {
      setLoading(true);
      Promise.all([
        getParcel(+id),
        api.get<IssuanceInfo | null>(`/parcels/${id}/issuance`).catch(() => ({ data: null })),
      ])
        .then(([p, iss]) => {
          setParcel(p.data);
          setNewStatus(p.data.status);
          setIssuance(iss.data);
        })
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleStatusChange = async () => {
    try {
      await updateParcelStatus(+id!, newStatus as ParcelStatus);
      const { data } = await getParcel(+id!);
      setParcel(data);
      message.success("Статус обновлён");
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    }
  };

  if (loading) return <Skeleton active />;
  if (!parcel) return <EmptyState title="Посылка не найдена" />;

  const isIssued = parcel.status === "issued";

  return (
    <>
      <PageHeader
        title={`Посылка #${parcel.id}`}
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

      <div className="animate-fade-in-up">
        <Card className="hover-card">
          <Descriptions
            bordered
            column={{ xs: 1, sm: 2 }}
            labelStyle={{ fontWeight: 600, color: "#637381", background: "#F9FAFB" }}
            contentStyle={{ background: "#fff" }}
          >
            <Descriptions.Item label="Трек-код">
              <TrackChip value={parcel.track_id} />
            </Descriptions.Item>
            <Descriptions.Item label="Статус">
              <StatusTag status={parcel.status as ParcelStatus} />
            </Descriptions.Item>
            <Descriptions.Item label="Client ID">{parcel.client_id}</Descriptions.Item>
            <Descriptions.Item label="Метод">
              <MethodTag method={parcel.delivery_method} />
            </Descriptions.Item>
            <Descriptions.Item label="Вес">
              {parcel.weight_kg != null && Number(parcel.weight_kg) > 0 ? <WeightCell value={parcel.weight_kg} /> : "—"}
            </Descriptions.Item>
            <Descriptions.Item label="Объём">{parcel.volume_m3 ? `${parcel.volume_m3} м³` : "—"}</Descriptions.Item>
            <Descriptions.Item label="Сумма">
              {parcel.amount_due ? <MoneyCell value={parcel.amount_due} /> : "—"}
            </Descriptions.Item>
            <Descriptions.Item label="Тариф">
              {parcel.tariff_snapshot ? <MoneyCell value={parcel.tariff_snapshot} /> : "—"}
            </Descriptions.Item>
            <Descriptions.Item label="Регистрация Китай">
              <Tag color={parcel.has_china_registration ? "success" : "default"}>
                {parcel.has_china_registration ? "Да" : "Нет"}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Комментарий">{parcel.comment || "—"}</Descriptions.Item>
            <Descriptions.Item label="Дата создания">{parcel.created_at?.slice(0, 10)}</Descriptions.Item>
            <Descriptions.Item label="Уведомлён">{parcel.notified_at?.slice(0, 10) || "—"}</Descriptions.Item>
          </Descriptions>

          {!isIssued && (
            <div style={{ marginTop: 20, display: "flex", gap: 12, alignItems: "center" }}>
              <Select
                value={newStatus}
                onChange={setNewStatus}
                style={{ width: 220 }}
                options={Object.entries(statusLabels).map(([k, v]) => ({ value: k, label: v }))}
              />
              <Button
                type="primary"
                onClick={handleStatusChange}
                disabled={newStatus === parcel.status}
                style={{ borderRadius: 10 }}
              >
                Обновить статус
              </Button>
            </div>
          )}

          {isIssued && (
            <Alert
              type="info"
              showIcon
              style={{ marginTop: 20 }}
              message="Посылка уже выдана"
              description="Изменить статус выданной посылки через эту страницу нельзя. Если выдача была ошибочной — нужна отдельная процедура отмены."
            />
          )}
        </Card>

        {issuance && (
          <Card
            className="hover-card"
            style={{ marginTop: 20 }}
            title={<span style={{ fontWeight: 600 }}>Информация о выдаче #{issuance.order_id}</span>}
          >
            <Descriptions
              bordered
              column={{ xs: 1, sm: 2 }}
              labelStyle={{ fontWeight: 600, color: "#637381", background: "#F9FAFB" }}
              contentStyle={{ background: "#fff" }}
            >
              <Descriptions.Item label="Дата выдачи">
                {new Date(issuance.issued_at).toLocaleString("ru-RU")}
              </Descriptions.Item>
              <Descriptions.Item label="Оплата">
                <Tag color={issuance.payment_status === "paid" ? "success" : "error"}>
                  {issuance.payment_status === "paid" ? "Оплачено" : "Долг"}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Способ оплаты">
                {issuance.payment_method === "cash"
                  ? "Наличные"
                  : issuance.payment_method === "card"
                  ? "Карта"
                  : issuance.payment_method === "transfer"
                  ? "Перевод"
                  : "—"}
              </Descriptions.Item>
              <Descriptions.Item label="Сумма по этой посылке">
                <MoneyCell value={issuance.amount} />
              </Descriptions.Item>
              {issuance.custom_price !== null && (
                <Descriptions.Item label="Изменённая цена">
                  <Tag color="warning">
                    <MoneyCell value={issuance.custom_price} />
                  </Tag>
                </Descriptions.Item>
              )}
              <Descriptions.Item label="Комментарий к выдаче" span={2}>
                {issuance.comment ? (
                  <span style={{ whiteSpace: "pre-wrap" }}>{issuance.comment}</span>
                ) : (
                  <span style={{ color: "#919EAB" }}>—</span>
                )}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}
      </div>
    </>
  );
}
