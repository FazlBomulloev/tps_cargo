import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider } from "antd";
import ruRU from "antd/locale/ru_RU";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
import App from "./App";
import ErrorBoundary from "./components/ErrorBoundary";
import "@fontsource-variable/inter/standard.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
import "./styles/tokens.css";
import "./global.css";

dayjs.extend(utc);
dayjs.extend(timezone);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={ruRU}
      theme={{
        token: {
          colorPrimary: "#00A76F",
          colorSuccess: "#00A76F",
          colorWarning: "#FFAB00",
          colorError: "#FF5630",
          colorInfo: "#00B8D9",
          colorBgContainer: "#FFFFFF",
          colorBgLayout: "#F4F6F8",
          colorText: "#0F1419",
          colorTextSecondary: "#5B6B7B",
          colorBorder: "rgba(145, 158, 171, 0.32)",
          colorBorderSecondary: "rgba(145, 158, 171, 0.16)",
          borderRadius: 10,
          borderRadiusSM: 6,
          borderRadiusLG: 12,
          fontFamily: "var(--font-sans)",
          fontSize: 14,
          fontSizeSM: 12,
          fontSizeLG: 16,
          controlHeight: 40,
          controlHeightSM: 32,
          controlHeightLG: 48,
          motionDurationMid: "200ms",
          motionDurationFast: "120ms",
        },
        components: {
          Button: { borderRadius: 10, controlHeight: 40, fontWeight: 600 },
          Card: { borderRadiusLG: 16, paddingLG: 24 },
          Input: { borderRadius: 10, controlHeight: 40 },
          Select: { borderRadius: 10, controlHeight: 40 },
          Table: {
            borderRadiusLG: 12,
            headerBg: "#F4F6F8",
            headerColor: "#5B6B7B",
            rowHoverBg: "rgba(0, 167, 111, 0.04)",
          },
          Tag: { borderRadiusSM: 6 },
          Modal: { borderRadiusLG: 16 },
          Menu: { itemBorderRadius: 8 },
          Popover: { borderRadiusLG: 12 },
          Alert: { borderRadiusLG: 10 },
        },
      }}
    >
      <ErrorBoundary>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ErrorBoundary>
    </ConfigProvider>
  </React.StrictMode>,
);
