import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import { Spin } from "antd";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import RequirePermission from "./components/RequirePermission";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import Forbidden from "./pages/Forbidden";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const ParcelsChina = lazy(() => import("./pages/ParcelsChina"));
const ParcelsDushanbe = lazy(() => import("./pages/ParcelsDushanbe"));
const ParcelsList = lazy(() => import("./pages/ParcelsList"));
const ParcelDetail = lazy(() => import("./pages/ParcelDetail"));
const Issuance = lazy(() => import("./pages/Issuance"));
const IssuanceHistory = lazy(() => import("./pages/IssuanceHistory"));
const Clients = lazy(() => import("./pages/Clients"));
const ClientDetail = lazy(() => import("./pages/ClientDetail"));
const Unresolved = lazy(() => import("./pages/Unresolved"));
const Warehouses = lazy(() => import("./pages/Warehouses"));
const Tariffs = lazy(() => import("./pages/Tariffs"));
const Staff = lazy(() => import("./pages/Staff"));
const Settings = lazy(() => import("./pages/Settings"));
const AuditLog = lazy(() => import("./pages/AuditLog"));
const Profile = lazy(() => import("./pages/Profile"));
const Expenses = lazy(() => import("./pages/Expenses"));

function PageFallback() {
  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "60vh" }}>
      <Spin size="large" />
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/403" element={<Forbidden />} />
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<RequirePermission page="dashboard"><Dashboard /></RequirePermission>} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/parcels-china" element={<RequirePermission page="parcels_china"><ParcelsChina /></RequirePermission>} />
          <Route path="/parcels-dushanbe" element={<RequirePermission page="parcels_dushanbe"><ParcelsDushanbe /></RequirePermission>} />
          <Route path="/parcels" element={<RequirePermission page="parcels_list"><ParcelsList /></RequirePermission>} />
          <Route path="/parcels/:id" element={<RequirePermission page="parcels_list"><ParcelDetail /></RequirePermission>} />
          <Route path="/issuance" element={<RequirePermission page="issuance"><Issuance /></RequirePermission>} />
          <Route path="/issuance-history" element={<RequirePermission page="issuance_history"><IssuanceHistory /></RequirePermission>} />
          <Route path="/clients" element={<RequirePermission page="clients"><Clients /></RequirePermission>} />
          <Route path="/clients/:id" element={<RequirePermission page="clients"><ClientDetail /></RequirePermission>} />
          <Route path="/unresolved" element={<RequirePermission page="unresolved"><Unresolved /></RequirePermission>} />
          <Route path="/warehouses" element={<RequirePermission page="warehouses"><Warehouses /></RequirePermission>} />
          <Route path="/tariffs" element={<RequirePermission page="tariffs"><Tariffs /></RequirePermission>} />
          <Route path="/expenses" element={<RequirePermission page="expenses"><Expenses /></RequirePermission>} />
          <Route path="/staff" element={<RequirePermission page="staff"><Staff /></RequirePermission>} />
          <Route path="/settings" element={<RequirePermission page="settings"><Settings /></RequirePermission>} />
          <Route path="/audit" element={<RequirePermission page="audit"><AuditLog /></RequirePermission>} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
