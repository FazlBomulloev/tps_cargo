import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { usePermissions } from "../hooks/usePermissions";

interface Props {
  page: string;
  children: ReactNode;
}

export default function RequirePermission({ page, children }: Props) {
  const { can, role } = usePermissions();
  if (role === null) return null;
  if (!can(page)) return <Navigate to="/403" replace />;
  return <>{children}</>;
}
