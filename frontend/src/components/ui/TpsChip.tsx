export interface TpsChipProps {
  value: string;
}

export function TpsChip({ value }: TpsChipProps) {
  return (
    <span
      className="track-chip"
      style={{
        background: "var(--c-bg-muted)",
        color: "var(--c-text-secondary)",
      }}
    >
      {value}
    </span>
  );
}
