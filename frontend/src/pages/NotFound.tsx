import { Button, Result } from "antd";
import { Link } from "react-router-dom";

export default function NotFound() {
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
        status="404"
        title={<span style={{ fontWeight: 700, letterSpacing: "-0.02em" }}>404</span>}
        subTitle={<span style={{ color: "var(--c-text-secondary)" }}>Страница не найдена</span>}
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
