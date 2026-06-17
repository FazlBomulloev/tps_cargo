import { Tooltip, message } from "antd";
import { CopyOutlined } from "@ant-design/icons";

export interface TrackChipProps {
  value: string;
  copyable?: boolean;
}

// navigator.clipboard.writeText доступен только в secure contexts
// (https + localhost). На http по IP/домену он undefined, поэтому
// используем fallback через скрытый textarea + execCommand("copy").
async function copyText(value: string): Promise<boolean> {
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(value);
      return true;
    } catch {
      // fall through to fallback
    }
  }
  const ta = document.createElement("textarea");
  ta.value = value;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.top = "-9999px";
  ta.style.left = "0";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  ta.setSelectionRange(0, value.length);
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  document.body.removeChild(ta);
  return ok;
}

export function TrackChip({ value, copyable = true }: TrackChipProps) {
  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    const ok = await copyText(value);
    if (ok) message.success("Скопировано");
    else message.error("Не удалось скопировать");
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
