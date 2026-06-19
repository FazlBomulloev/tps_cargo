export type Money = number;
export type Weight = number;
export type Volume = number;

export type ParcelStatus = "in_china" | "received_dushanbe" | "issued" | "unresolved";
export type DeliveryMethod = "avia" | "truck";
export type Role = "owner" | "admin_china" | "admin_dushanbe" | "staff";

// Mirror backend VALID_PERMISSIONS + utils/permissions.ts.
export type PermissionKey =
  | "dashboard"
  | "parcels_china"
  | "parcels_dushanbe"
  | "parcels_list"
  | "parcels_delete"
  | "issuance"
  | "issuance_history"
  | "clients"
  | "unresolved"
  | "warehouses"
  | "tariffs"
  | "staff"
  | "settings"
  | "audit"
  | "expenses";

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface Client {
  id: number;
  telegram_id: number;
  tps_code: string;
  full_name: string;
  phone: string;
  address: string | null;
  lang: string;
  status: string;
  created_at: string;
  last_activity_at: string | null;
}

export interface ParcelChina {
  id: number;
  track_id: string;
  warehouse_id: number | null;
  created_by: number;
  created_at: string;
}

export interface ParcelDushanbe {
  id: number;
  track_id: string;
  client_id: number;
  client_name?: string | null;
  tps_code?: string | null;
  status: ParcelStatus;
  weight_kg: Weight | null;
  volume_m3: Volume | null;
  delivery_method: DeliveryMethod;
  warehouse_id: number | null;
  amount_due: Money | null;
  tariff_snapshot: Money | null;
  has_china_registration: boolean;
  comment: string | null;
  shelf: string | null;
  notified_at: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface Tariff {
  id: number;
  method: DeliveryMethod;
  price_per_kg: Money;
  price_per_m3: Money | null;
  currency: string;
  is_active: boolean;
  created_by: number;
  created_at: string;
}

export interface IssuanceItem {
  id: number;
  parcel_id: number;
  track_id: string | null;
  weight_kg: Weight;
  volume_m3: Volume | null;
  delivery_method: DeliveryMethod;
  tariff_applied: Money;
  custom_price: Money | null;
  amount: Money;
}

export interface IssuanceOrder {
  id: number;
  client_id: number;
  client_name: string | null;
  tps_code: string | null;
  staff_id: number;
  total_weight: Weight;
  total_amount: Money;
  payment_status: string;
  payment_method: string | null;
  comment: string | null;
  issued_at: string;
  items: IssuanceItem[];
}

export interface Expense {
  id: number;
  amount: Money;
  category: DeliveryMethod;
  comment: string | null;
  created_by: number;
  created_at: string;
}

export interface Warehouse {
  id: number;
  name: string;
  type: string;
  country: string | null;
  city: string | null;
  phone: string;
  region: string;
  address: string;
  is_active: boolean;
  created_at: string;
}

// password_hash intentionally omitted — never sent by the backend.
export interface StaffUser {
  id: number;
  full_name: string;
  login: string;
  role: Role;
  avatar_url: string | null;
  permissions: PermissionKey[];
  warehouse_id: number | null;
  is_active: boolean;
  created_at: string;
}

export interface Setting {
  key: string;
  value: string;
  updated_at: string;
  updated_by: number | null;
}

export interface NotificationLog {
  id: number;
  client_id: number;
  parcel_id: number | null;
  notification_type: string;
  status: string;
  error: string | null;
  sent_at: string;
}

export interface AuditLog {
  id: number;
  staff_id: number;
  action: string;
  entity_type: string;
  entity_id: number | null;
  before_json: Record<string, unknown> | null;
  after_json: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface OverviewStats {
  china_count: number;
  dushanbe_count: number;
  issued_count: number;
  unresolved_count: number;
  added_count: number;
  gross_revenue: Money;
  total_expenses: Money;
  revenue: Money;
  expense_by_category: Record<string, Money>;
  revenue_by_method: Record<string, Money>;
}

export interface ParcelsByDayPoint {
  date: string;
  count: number;
  weight: Weight;
}

export interface RevenuePoint {
  date: string;
  revenue: Money;
  expenses: Money;
  profit: Money;
}

export interface TopClient {
  client_id: number;
  full_name: string;
  tps_code: string;
  count: number;
  total_weight: Weight;
  total_amount: Money;
}

export interface StuckParcel {
  id: number;
  track_id: string;
  client_id: number;
  client_name: string | null;
  tps_code: string | null;
  days: number;
  weight_kg: Weight;
  created_at: string;
}

export interface StaffActivityRow {
  staff_id: number;
  full_name: string;
  role: Role;
  parcels_added: number;
  issuances: number;
  amount_issued: Money;
}

export interface UnresolvedParcel {
  id: number;
  track_id: string;
  raw_tps_code: string;
  weight_kg: Weight | null;
  volume_m3: Volume | null;
  delivery_method: DeliveryMethod | null;
  comment: string | null;
  resolved: boolean;
  resolved_parcel_id: number | null;
  created_by: number;
  created_at: string;
}
