import { Button, Result } from "antd";
import { Link } from "react-router-dom";

export default function Forbidden() {
  return (
    <div
      style={{
        minHeight: "60vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "var(--s-5)",
      }}
    >
      <Result
        status="403"
        title={<span style={{ fontWeight: 700, letterSpacing: "-0.02em" }}>403</span>}
        subTitle={
          <span style={{ color: "var(--c-text-secondary)" }}>
            Недостаточно прав для просмотра раздела
          </span>
        }
        extra={
          <Link to="/">
            <Button type="primary" size="large">
              На главную
            </Button>
          </Link>
        }
      />
    </div>
  );
}
