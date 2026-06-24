import { useEffect, useState } from "react";
import { Table, Button, Modal, Form, InputNumber, Select, message, Card } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { getActiveTariffs, createTariff } from "../api/tariffs";
import type { DeliveryMethod } from "../types/api";
import { PageHeader, MethodTag, MoneyCell } from "../components/ui";
import { formatDateRu } from "../utils/format";

export default function Tariffs() {
  const [items, setItems] = useState<any[]>([]);
  const [modal, setModal] = useState(false);
  const [form] = Form.useForm();

  const load = () => getActiveTariffs().then((r) => setItems(r.data));
  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    const values = await form.validateFields();
    try {
      await createTariff(values);
      message.success("Тариф создан (старый деактивирован)");
      setModal(false); form.resetFields(); load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    }
  };

  return (
    <>
      <PageHeader
        title="Тарифы"
        actions={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => { form.resetFields(); setModal(true); }}
            style={{ borderRadius: 10, height: 44 }}
          >
            Новый тариф
          </Button>
        }
      />

      <div className="animate-fade-in-up">
        <Card styles={{ body: { padding: 0 } }} className="hover-card">
          <Table
            dataSource={items}
            rowKey="id"
            columns={[
              {
                title: "Метод",
                dataIndex: "method",
                render: (v: DeliveryMethod) => <MethodTag method={v} />,
              },
              {
                title: "TJS/кг",
                dataIndex: "price_per_kg",
                render: (v: number) => <MoneyCell value={v} />,
              },
              {
                title: "TJS/м³",
                dataIndex: "price_per_m3",
                render: (v: number) => (v ? <MoneyCell value={v} /> : "—"),
              },
              { title: "Валюта", dataIndex: "currency" },
              {
                title: "Дата",
                dataIndex: "created_at",
                render: (v: string) => formatDateRu(v),
              },
            ]}
          />
        </Card>
      </div>

      <Modal
        title="Новый тариф"
        open={modal}
        onOk={handleCreate}
        onCancel={() => setModal(false)}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="method" label="Метод" rules={[{ required: true }]}>
            <Select options={[
              { value: "avia", label: "Авиа" },
              { value: "truck", label: "Фура" },
            ]} />
          </Form.Item>
          <Form.Item name="price_per_kg" label="Цена за кг (TJS)" rules={[{ required: true }]}>
            <InputNumber min={0} step={0.5} precision={2} decimalSeparator="." style={{ width: "100%", borderRadius: 10 }} />
          </Form.Item>
          <Form.Item name="price_per_m3" label="Цена за м³ (TJS)">
            <InputNumber min={0} step={10} precision={2} decimalSeparator="." style={{ width: "100%", borderRadius: 10 }} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
