import { useEffect, useState } from "react";
import {
  Card,
  Form,
  InputNumber,
  Select,
  Input,
  Button,
  Table,
  Tag,
  message,
  Typography,
  Statistic,
  Popconfirm,
  Space,
} from "antd";
import { SaveOutlined, DeleteOutlined } from "@ant-design/icons";
import { useAuthStore } from "../store/authStore";
import { createExpense, deleteExpense, getExpenses } from "../api/expenses";

const categoryTag = (v: string) => (
  <Tag
    color={v === "avia" ? "blue" : "orange"}
    style={{ borderRadius: 20, padding: "2px 12px" }}
  >
    {v === "avia" ? "Авиа" : "Фура"}
  </Tag>
);

export default function Expenses() {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [totalSum, setTotalSum] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);
  const user = useAuthStore((s) => s.user);
  const canDelete = user?.role === "owner";

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await getExpenses({ page, per_page: perPage });
      setItems(data.items || []);
      setTotal(data.total || 0);
      setTotalSum(data.total_sum || 0);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [page, perPage]);

  const onFinish = async (values: any) => {
    setSubmitting(true);
    try {
      await createExpense({
        amount: values.amount,
        category: values.category,
        comment: values.comment?.trim() || undefined,
      });
      message.success("Расход сохранён");
      form.resetFields();
      // Возвращаемся на первую страницу, чтобы свежая запись была видна.
      if (page !== 1) setPage(1);
      else load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка сохранения");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteExpense(id);
      message.success("Расход удалён");
      load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка удаления");
    }
  };

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Расходы
        </Typography.Title>
        <Statistic
          title="Итого по фильтру"
          value={totalSum.toFixed(2)}
          suffix="TJS"
          valueStyle={{ fontWeight: 700, color: "#FF5630" }}
        />
      </div>

      <div className="stagger-children">
        <Card className="hover-card" style={{ marginBottom: 20 }}>
          <Form form={form} layout="vertical" onFinish={onFinish}>
            <Space wrap style={{ width: "100%" }} size={16}>
              <Form.Item
                name="amount"
                label="Сумма (TJS)"
                rules={[{ required: true, message: "Укажите сумму" }]}
                style={{ minWidth: 200, flex: 1, marginBottom: 0 }}
              >
                <InputNumber
                  min={0.01}
                  step={1}
                  style={{ width: "100%", borderRadius: 10 }}
                  placeholder="0.00"
                />
              </Form.Item>

              <Form.Item
                name="category"
                label="Категория"
                rules={[{ required: true, message: "Выберите категорию" }]}
                style={{ minWidth: 180, marginBottom: 0 }}
              >
                <Select
                  placeholder="Категория"
                  options={[
                    { value: "avia", label: "Авиа" },
                    { value: "truck", label: "Фура" },
                  ]}
                />
              </Form.Item>

              <Form.Item
                name="comment"
                label="Комментарий"
                style={{ minWidth: 280, flex: 2, marginBottom: 0 }}
              >
                <Input placeholder="Например: топливо, аренда…" />
              </Form.Item>

              <Form.Item label=" " style={{ marginBottom: 0 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={submitting}
                  icon={<SaveOutlined />}
                  style={{ borderRadius: 10, height: 40 }}
                >
                  Сохранить
                </Button>
              </Form.Item>
            </Space>
          </Form>
        </Card>

        <Card
          bodyStyle={{ padding: 0 }}
          className="hover-card"
          title={<span style={{ fontWeight: 600 }}>История расходов</span>}
        >
          <Table
            dataSource={items}
            rowKey="id"
            loading={loading}
            pagination={{
              current: page,
              pageSize: perPage,
              total,
              onChange: (p, ps) => {
                setPage(p);
                setPerPage(ps);
              },
              showSizeChanger: true,
              pageSizeOptions: [10, 20, 50, 100],
            }}
            columns={[
              {
                title: "Дата",
                dataIndex: "created_at",
                width: 160,
                render: (v: string) =>
                  v ? new Date(v).toLocaleString("ru-RU") : "—",
              },
              {
                title: "Категория",
                dataIndex: "category",
                width: 110,
                render: categoryTag,
              },
              {
                title: "Сумма",
                dataIndex: "amount",
                width: 140,
                render: (v: number) => (
                  <span style={{ fontWeight: 600, color: "#FF5630" }}>
                    −{Number(v).toFixed(2)} TJS
                  </span>
                ),
              },
              { title: "Комментарий", dataIndex: "comment", ellipsis: true },
              {
                title: "Кем добавлен",
                dataIndex: "created_by_name",
                width: 180,
                render: (v: string) => v || "—",
              },
              ...(canDelete
                ? [
                    {
                      title: "",
                      width: 60,
                      render: (_: any, r: any) => (
                        <Popconfirm
                          title="Удалить расход?"
                          onConfirm={() => handleDelete(r.id)}
                          okText="Да"
                          cancelText="Нет"
                        >
                          <Button
                            type="text"
                            danger
                            icon={<DeleteOutlined />}
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
