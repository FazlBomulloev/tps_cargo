import { Tag } from "antd";
import type { ParcelStatus } from "../../types/api";

const STATUS_LABELS: Record<ParcelStatus, string> = {
  in_china: "В Китае",
  received_dushanbe: "В Душанбе",
  issued: "Выдано",
  unresolved: "Неопознанная",
};
const STATUS_COLORS: Record<ParcelStatus, string> = {
  in_china: "cyan",
  received_dushanbe: "processing",
  issued: "success",
  unresolved: "warning",
};

export function StatusTag({ status }: { status: ParcelStatus }) {
  return <Tag color={STATUS_COLORS[status]}>{STATUS_LABELS[status]}</Tag>;
}
