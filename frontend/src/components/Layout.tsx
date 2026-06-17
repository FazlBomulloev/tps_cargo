import { useState } from "react";
import type { ReactNode } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Layout as AntLayout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Drawer,
  Grid,
} from "antd";
import type { MenuProps } from "antd";
import {
  DashboardOutlined,
  InboxOutlined,
  ContainerOutlined,
  UnorderedListOutlined,
  ShoppingCartOutlined,
  HistoryOutlined,
  TeamOutlined,
  ShopOutlined,
  WarningOutlined,
  DollarOutlined,
  WalletOutlined,
  SettingOutlined,
  FileSearchOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MenuOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useAuth } from "../hooks/useAuth";
import { usePermissions } from "../hooks/usePermissions";
import { BrandLogo } from "./BrandLogo";
import { ROLE_COLORS, ROLE_LABELS } from "../constants/roles";

const { Sider, Header, Content } = AntLayout;
const { useBreakpoint } = Grid;

function SidebarGroupLabel({ children }: { children: ReactNode }) {
  return (
    <span
      style={{
        fontSize: "var(--text-xs)",
        fontWeight: 600,
        letterSpacing: "0.06em",
        color: "var(--c-sidebar-text-muted)",
        textTransform: "uppercase",
        padding: "0 12px",
      }}
    >
      {children}
    </span>
  );
}

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { user, logout } = useAuth();
  const { can } = usePermissions();
  const location = useLocation();
  const navigate = useNavigate();
  const screens = useBreakpoint();
  const isMobile = !screens.lg;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const menuItems: MenuProps["items"] = [
    {
      type: "group" as const,
      label: <SidebarGroupLabel>Операции</SidebarGroupLabel>,
      children: [
        can("dashboard") && {
          key: "/",
          icon: <DashboardOutlined />,
          label: <Link to="/">Дашборд</Link>,
        },
        can("parcels_china") && {
          key: "/parcels-china",
          icon: <InboxOutlined />,
          label: <Link to="/parcels-china">Склад Китай</Link>,
        },
        can("parcels_dushanbe") && {
          key: "/parcels-dushanbe",
          icon: <ContainerOutlined />,
          label: <Link to="/parcels-dushanbe">Склад Душанбе</Link>,
        },
        can("parcels_list") && {
          key: "/parcels",
          icon: <UnorderedListOutlined />,
          label: <Link to="/parcels">Все посылки</Link>,
        },
        can("issuance") && {
          key: "/issuance",
          icon: <ShoppingCartOutlined />,
          label: <Link to="/issuance">Выдача</Link>,
        },
        can("issuance_history") && {
          key: "/issuance-history",
          icon: <HistoryOutlined />,
          label: <Link to="/issuance-history">История</Link>,
        },
      ].filter(Boolean),
    },
    {
      type: "group" as const,
      label: <SidebarGroupLabel>Учёт</SidebarGroupLabel>,
      children: [
        can("clients") && {
          key: "/clients",
          icon: <TeamOutlined />,
          label: <Link to="/clients">Клиенты</Link>,
        },
        can("warehouses") && {
          key: "/warehouses",
          icon: <ShopOutlined />,
          label: <Link to="/warehouses">Склады</Link>,
        },
        can("tariffs") && {
          key: "/tariffs",
          icon: <DollarOutlined />,
          label: <Link to="/tariffs">Тарифы</Link>,
        },
        can("expenses") && {
          key: "/expenses",
          icon: <WalletOutlined />,
          label: <Link to="/expenses">Расходы</Link>,
        },
        can("unresolved") && {
          key: "/unresolved",
          icon: <WarningOutlined />,
          label: <Link to="/unresolved">Неопознанные</Link>,
        },
      ].filter(Boolean),
    },
    {
      type: "group" as const,
      label: <SidebarGroupLabel>Команда</SidebarGroupLabel>,
      children: [
        can("staff") && {
          key: "/staff",
          icon: <UserOutlined />,
          label: <Link to="/staff">Сотрудники</Link>,
        },
      ].filter(Boolean),
    },
    {
      type: "group" as const,
      label: <SidebarGroupLabel>Система</SidebarGroupLabel>,
      children: [
        can("settings") && {
          key: "/settings",
          icon: <SettingOutlined />,
          label: <Link to="/settings">Настройки</Link>,
        },
        can("audit") && {
          key: "/audit",
          icon: <FileSearchOutlined />,
          label: <Link to="/audit">Журнал</Link>,
        },
      ].filter(Boolean),
    },
  ]
    .map((g) => ({ ...g, children: g.children.filter(Boolean) as any[] }))
    .filter((g) => g.children.length > 0);

  const userMenuItems = [
    {
      key: "profile",
      icon: <UserOutlined />,
      label: "Профиль",
      onClick: () => navigate("/profile"),
    },
    {
      key: "settings",
      icon: <SettingOutlined />,
      label: "Настройки",
      onClick: () => navigate("/settings"),
    },
    { type: "divider" as const },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "Выйти",
      danger: true,
      onClick: handleLogout,
    },
  ];

  const sidebarMenu = (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[location.pathname]}
      items={menuItems}
      style={{ marginTop: 8, background: "transparent", borderInlineEnd: 0 }}
      onClick={() => setDrawerOpen(false)}
    />
  );

  const userCard = (
    <div
      style={{
        margin: collapsed ? "12px 8px" : "12px 16px",
        padding: collapsed ? "12px 8px" : "14px 16px",
        background: "rgba(145, 158, 171, 0.08)",
        borderRadius: "var(--radius-lg)",
        display: "flex",
        alignItems: "center",
        gap: 12,
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        overflow: "hidden",
      }}
    >
      <Avatar
        size={36}
        src={user?.avatar_url || undefined}
        style={{
          background: (user?.role ? ROLE_COLORS[user.role] : undefined) || "var(--c-primary)",
          flexShrink: 0,
          fontSize: 14,
          fontWeight: 600,
        }}
      >
        {!user?.avatar_url && (user?.full_name?.charAt(0)?.toUpperCase() || "U")}
      </Avatar>
      {!collapsed && (
        <div style={{ overflow: "hidden", minWidth: 0 }}>
          <div
            style={{
              color: "#fff",
              fontWeight: 600,
              fontSize: 14,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {user?.full_name}
          </div>
          <div
            style={{
              color: "var(--c-sidebar-text-muted)",
              fontSize: 12,
            }}
          >
            {(user?.role ? ROLE_LABELS[user.role] : undefined) || user?.role}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <AntLayout style={{ minHeight: "100vh" }}>
      {!isMobile && (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          breakpoint="lg"
          width={280}
          collapsedWidth={80}
          className="custom-sidebar"
          trigger={null}
          style={{
            background: "var(--c-sidebar-bg)",
            overflow: "auto",
            height: "100vh",
            position: "fixed",
            left: 0,
            top: 0,
            bottom: 0,
            zIndex: 100,
            transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
            borderRight: "1px solid var(--c-border)",
          }}
        >
          <BrandLogo collapsed={collapsed} />
          {userCard}
          {sidebarMenu}
        </Sider>
      )}

      {isMobile && (
        <Drawer
          open={drawerOpen}
          placement="left"
          onClose={() => setDrawerOpen(false)}
          width={280}
          closable={false}
          styles={{ body: { padding: 0, background: "var(--c-sidebar-bg)" } }}
        >
          <BrandLogo />
          {userCard}
          {sidebarMenu}
        </Drawer>
      )}

      <AntLayout
        style={{
          marginLeft: isMobile ? 0 : collapsed ? 80 : 280,
          transition: "margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
          background: "var(--c-bg-app)",
        }}
      >
        <Header
          className="main-header"
          style={{
            padding: "0 24px",
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            position: "sticky",
            top: 0,
            zIndex: 99,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <Button
              type="text"
              icon={
                isMobile ? (
                  <MenuOutlined />
                ) : collapsed ? (
                  <MenuUnfoldOutlined />
                ) : (
                  <MenuFoldOutlined />
                )
              }
              onClick={() => (isMobile ? setDrawerOpen(true) : setCollapsed(!collapsed))}
              aria-label={isMobile ? "Открыть меню" : "Свернуть меню"}
              style={{
                fontSize: 18,
                width: 40,
                height: 40,
                borderRadius: "var(--radius-md)",
              }}
            />
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              trigger={["click"]}
            >
              <div
                className="layout-user"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "6px 12px",
                  borderRadius: "var(--radius-md)",
                  marginLeft: 4,
                }}
              >
                <Avatar
                  size={36}
                  src={user?.avatar_url || undefined}
                  style={{
                    background: (user?.role ? ROLE_COLORS[user.role] : undefined) || "var(--c-primary)",
                    fontWeight: 600,
                  }}
                >
                  {!user?.avatar_url && (user?.full_name?.charAt(0)?.toUpperCase() || "U")}
                </Avatar>
                <div style={{ lineHeight: 1.3, textAlign: "right" }}>
                  <div
                    title={user?.full_name}
                    style={{
                      fontWeight: 600,
                      fontSize: 14,
                      color: "var(--c-text)",
                      maxWidth: 200,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {user?.full_name}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--c-text-muted)" }}>
                    {(user?.role ? ROLE_LABELS[user.role] : undefined) || user?.role}
                  </div>
                </div>
              </div>
            </Dropdown>
          </div>
        </Header>

        <Content
          style={{
            margin: isMobile ? "var(--s-4)" : "var(--s-5)",
            minHeight: "calc(100vh - 64px - 48px)",
          }}
        >
          <div className="page-content">
            <Outlet />
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
