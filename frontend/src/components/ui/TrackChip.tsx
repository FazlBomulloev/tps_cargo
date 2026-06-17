import { Tooltip, message } from "antd";
import { CopyOutlined } from "@ant-design/icons";

export interface TrackChipProps {
  value: string;
  copyable?: boolean;
}

export function TrackChip({ value, copyable = true }: TrackChipProps) {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      message.success("Скопировано");
    } catch {
      message.error("Не удалось скопировать");
    }
  };
  return (
    <Tooltip title={copyable ? "Кликни, чтобы скопировать" : undefined}>
      <span
        onClick={copyable ? handleCopy : undefined}
        className="track-chip"
        style={{
          background: "var(--c-primary-soft)",
          color: "var(--c-text)",
          cursor: copyable ? "pointer" : "default",
        }}
      >
        {value}
        {copyable && <CopyOutlined style={{ fontSize: 10, opacity: 0.5 }} />}
      </span>
    </Tooltip>
  );
}
