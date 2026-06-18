import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Typography, Grid, message } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import axios from "axios";
import { login } from "../api/auth";
import { useAuth } from "../hooks/useAuth";
import { BrandLogo } from "../components/BrandLogo";

const { useBreakpoint } = Grid;

export default function Login() {
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuth();
  const navigate = useNavigate();
  const screens = useBreakpoint();
  const showBrandPanel = !!screens.lg;

  const onFinish = async (values: { login: string; password: string }) => {
    setLoading(true);
    try {
      const { data } = await login(values.login, values.password);
      const token = data.access_token;
      // Явный token минуя api-клиент: store обновляем атомарно (token+user).
      const { data: user } = await axios.get("/api/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAuth(token, user);
      navigate("/");
    } catch (err: any) {
      if (import.meta.env.DEV) {
        console.error("Login error detail:", err.response?.data || err.message);
      }
      message.error("Неверный логин или пароль");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "var(--c-bg-app)" }}>
      {showBrandPanel && (
        <div
          style={{
            flex: 1.2,
            background: "linear-gradient(135deg, #0F1419 0%, #1C252E 100%)",
            position: "relative",
            overflow: "hidden",
            display: "flex",
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundImage:
                "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
              backgroundSize: "32px 32px",
            }}
          />
          <div style={{ position: "absolute", top: 40, left: 40, zIndex: 1 }}>
            <BrandLogo />
          </div>
          <div style={{ position: "absolute", bottom: 48, left: 40, right: 40, color: "#fff" }}>
            <div
              style={{
                fontSize: "var(--text-2xl)",
                fontWeight: 700,
                lineHeight: 1.2,
                letterSpacing: "-0.02em",
                maxWidth: 480,
              }}
            >
              Логистика Китай — Душанбе. <br />
              <span style={{ color: "var(--c-primary)" }}>Без хаоса в треках.</span>
            </div>
            <div style={{ fontSize: "var(--text-sm)", color: "rgba(255,255,255,0.55)", marginTop: 12 }}>
              Cargo TPS — система учёта посылок, выдач и клиентов.
            </div>
          </div>
        </div>
      )}

      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "var(--s-5)",
        }}
      >
        <div style={{ width: "100%", maxWidth: 400 }}>
          {!showBrandPanel && (
            <div style={{ marginBottom: 32 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: "var(--radius-md)",
                    background: "var(--c-primary)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#fff",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    fontSize: 16,
                  }}
                >
                  Cg
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 16, letterSpacing: "-0.02em", color: "var(--c-text)" }}>
                    Cargo TPS
                  </div>
                  <div style={{ fontSize: 11, color: "var(--c-text-muted)" }}>CN → TJ logistics</div>
                </div>
              </div>
            </div>
          )}

          <Typography.Title
            level={3}
            style={{
              margin: 0,
              marginBottom: 8,
              fontWeight: 700,
              letterSpacing: "-0.02em",
              color: "var(--c-text)",
            }}
          >
            С возвращением
          </Typography.Title>
          <Typography.Text style={{ color: "var(--c-text-secondary)" }}>
            Войдите в панель управления
          </Typography.Text>

          <Form onFinish={onFinish} size="large" layout="vertical" style={{ marginTop: 32 }}>
            <Form.Item name="login" rules={[{ required: true, message: "Введите логин" }]}>
              <Input
                prefix={<UserOutlined style={{ color: "var(--c-text-muted)", fontSize: 18 }} />}
                placeholder="Логин"
                style={{
                  height: 48,
                  borderRadius: "var(--radius-md)",
                  fontSize: 15,
                }}
              />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, message: "Введите пароль" }]}>
              <Input.Password
                prefix={<LockOutlined style={{ color: "var(--c-text-muted)", fontSize: 18 }} />}
                placeholder="Пароль"
                style={{
                  height: 48,
                  borderRadius: "var(--radius-md)",
                  fontSize: 15,
                }}
              />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{
                  height: 48,
                  borderRadius: "var(--radius-md)",
                  fontSize: 16,
                  fontWeight: 600,
                  background: "var(--c-primary)",
                }}
              >
                Войти
              </Button>
            </Form.Item>
          </Form>
        </div>
      </div>
    </div>
  );
}
