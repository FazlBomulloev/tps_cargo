import type { ReactNode } from "react";
import { Tag } from "antd";
import { SendOutlined, CarOutlined } from "@ant-design/icons";
import type { DeliveryMethod } from "../../types/api";

const META: Record<DeliveryMethod, { label: string; icon: ReactNode; color: string }> = {
  avia: { label: "Авиа", icon: <SendOutlined />, color: "default" },
  truck: { label: "Фура", icon: <CarOutlined />, color: "default" },
};

export function MethodTag({ method }: { method: DeliveryMethod }) {
  const m = META[method];
  return (
    <Tag color={m.color} icon={m.icon}>
      {m.label}
    </Tag>
  );
}
