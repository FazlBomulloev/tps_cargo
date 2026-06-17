import { Skeleton } from "antd";

export function LazyChartFallback({ height = 300 }: { height?: number }) {
  return (
    <div style={{ width: "100%", height, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <Skeleton active paragraph={{ rows: 6 }} />
    </div>
  );
}
