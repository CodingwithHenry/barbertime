const BASE = "/api/v1";

function getToken(): string | null {
  return localStorage.getItem("token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.body && !(options.body instanceof FormData)
      ? { "Content-Type": "application/json" }
      : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> | undefined),
  };

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Auth
export const authApi = {
  register: (email: string, password: string, name: string) =>
    request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  verifyEmail: (code: string) =>
    request<{ message: string }>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ code }),
    }),
  resendVerification: () =>
    request<{ message: string }>("/auth/resend-verification", { method: "POST" }),
  forgotPassword: (email: string) =>
    request<{ message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  resetPassword: (email: string, code: string, new_password: string) =>
    request<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ email, code, new_password }),
    }),
};

// Shop dashboard
export const shopApi = {
  me: () => request<Shop>("/shops/me"),
  updateProfile: (data: Partial<Shop>) =>
    request<Shop>("/shops/me", { method: "PATCH", body: JSON.stringify(data) }),
  uploadPhoto: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<Shop>("/shops/me/photo", { method: "POST", body: fd });
  },
  updateStatus: (status: string, wait_time: number) =>
    request<Shop>("/shops/me/status", {
      method: "PATCH",
      body: JSON.stringify({ status, wait_time }),
    }),
  suggestWaitTime: (employee_id?: number) =>
    request<{ suggested_wait_time: number | null }>(
      `/shops/me/suggest-wait-time${employee_id ? `?employee_id=${employee_id}` : ""}`
    ),
};

// Employees
export const employeeApi = {
  list: () => request<Employee[]>("/employees/"),
  create: (name: string, role?: string) =>
    request<Employee>("/employees/", {
      method: "POST",
      body: JSON.stringify({ name, role }),
    }),
  update: (id: number, data: Partial<Employee>) =>
    request<Employee>(`/employees/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  uploadPhoto: (id: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<Employee>(`/employees/${id}/photo`, { method: "POST", body: fd });
  },
  delete: (id: number) => request<void>(`/employees/${id}`, { method: "DELETE" }),
  suggestWait: (id: number) =>
    request<{ suggested_wait_time: number | null }>(`/employees/${id}/suggest-wait-time`),
};

// Reservations
export const reservationApi = {
  list: () => request<Reservation[]>("/reservations/"),
  create: (shop_id: number, phone_number: string, employee_id?: number) =>
    request<Reservation>(`/reservations/${shop_id}`, {
      method: "POST",
      body: JSON.stringify({ phone_number, employee_id }),
    }),
  updateStatus: (id: number, new_status: string) =>
    request<Reservation>(`/reservations/${id}/status?new_status=${new_status}`, {
      method: "PATCH",
    }),
};

// Discounts
export const discountApi = {
  list: () => request<FlashDiscount[]>("/discounts/"),
  create: (data: Partial<FlashDiscount>) =>
    request<FlashDiscount>("/discounts/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<FlashDiscount>) =>
    request<FlashDiscount>(`/discounts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: number) => request<void>(`/discounts/${id}`, { method: "DELETE" }),
  redeem: (id: number) => request<FlashDiscount>(`/discounts/${id}/redeem`, { method: "POST" }),
};

// Stripe
export const stripeApi = {
  subscribe: () => request<{ url: string }>("/stripe/subscribe", { method: "POST" }),
  portal: () => request<{ url: string }>("/stripe/portal"),
};

// Public
export const publicApi = {
  listShops: (lat?: number, lon?: number) => {
    const params = lat != null && lon != null ? `?lat=${lat}&lon=${lon}` : "";
    return request<Shop[]>(`/public/shops${params}`);
  },
  getShop: (slug: string) => request<Shop>(`/public/shops/${slug}`),
  getEmployees: (slug: string) => request<Employee[]>(`/public/shops/${slug}/employees`),
  getDiscounts: (slug: string) => request<FlashDiscount[]>(`/public/shops/${slug}/discounts`),
};

// Types
export interface Shop {
  id: number;
  email?: string;
  name: string;
  slug: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  opening_hours?: Record<string, string>;
  photo_url?: string;
  description?: string;
  price_list?: { service: string; price: number }[];
  status: "open" | "busy" | "closed";
  wait_time: number;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
  subscription_status?: string;
  is_verified?: boolean;
  created_at?: string;
}

export interface Employee {
  id: number;
  shop_id: number;
  name: string;
  photo_url?: string;
  role?: string;
  wait_time: number;
  is_active: boolean;
}

export interface Reservation {
  id: number;
  shop_id: number;
  employee_id?: number;
  expires_at: string;
  status: "active" | "expired" | "cancelled" | "honoured";
}

export interface FlashDiscount {
  id: number;
  shop_id: number;
  title: string;
  description?: string;
  expires_at?: string;
  max_uses?: number;
  uses_count: number;
  is_active: boolean;
  created_at: string;
}
