import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { Spin } from "antd";
import { useAuth } from "../hooks/useAuth";
import { getMe } from "../api/auth";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, user, setAuth, logout } = useAuth();
  const [loading, setLoading] = useState(!!token && !user);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    if (user) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    getMe()
      .then(({ data }) => {
        if (!cancelled) setAuth(token, data);
      })
      .catch((err) => {
        if (cancelled) return;
        const status = err?.response?.status;
        if (status === 401 || status === 403) {
          logout();
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token, user, setAuth, logout]);

  if (!token) return <Navigate to="/login" replace />;
  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        <Spin size="large" />
      </div>
    );
  }
  return <>{children}</>;
}
