import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { publicApi, reservationApi, type Shop, type Employee, type FlashDiscount } from "../api";
import LangSwitcher from "../components/LangSwitcher";

export default function ShopDetail() {
  const { slug } = useParams<{ slug: string }>();
  const { t } = useTranslation();
  const qc = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);

  const { data: shop, isLoading } = useQuery({
    queryKey: ["shop", slug],
    queryFn: () => publicApi.getShop(slug!),
    enabled: !!slug,
  });

  const { data: employees = [] } = useQuery({
    queryKey: ["shop-employees", slug],
    queryFn: () => publicApi.getEmployees(slug!),
    enabled: !!slug,
  });

  const { data: discounts = [] } = useQuery({
    queryKey: ["shop-discounts", slug],
    queryFn: () => publicApi.getDiscounts(slug!),
    enabled: !!slug,
  });

  useEffect(() => {
    if (!shop) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/shops/${shop.id}`);
    wsRef.current = ws;
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "status_update" || msg.type === "initial") {
        qc.setQueryData(["shop", slug], (old: Shop | undefined) =>
          old ? { ...old, status: msg.status, wait_time: msg.wait_time } : old
        );
      }
    };
    return () => ws.close();
  }, [shop?.id]);

  const [phone, setPhone] = useState("");
  const [selectedEmployee, setSelectedEmployee] = useState<number | undefined>();
  const [reservationDone, setReservationDone] = useState(false);
  const [reservationError, setReservationError] = useState("");

  const reserveMutation = useMutation({
    mutationFn: () => reservationApi.create(shop!.id, phone, selectedEmployee),
    onSuccess: () => { setReservationDone(true); setReservationError(""); },
    onError: (err: Error) => setReservationError(err.message),
  });

  const STATUS_COLORS = {
    open: "bg-green-100 text-green-800",
    busy: "bg-yellow-100 text-yellow-800",
    closed: "bg-gray-100 text-gray-600",
  };

  if (isLoading) return (
    <div className="max-w-2xl mx-auto px-4 py-8 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-48 mb-4" />
      <div className="h-40 bg-gray-200 rounded" />
    </div>
  );

  if (!shop) return (
    <div className="max-w-2xl mx-auto px-4 py-8 text-center text-gray-400">Shop not found.</div>
  );

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-brand-600 hover:text-brand-700">{t("shop_detail.back")}</Link>
            <span className="font-bold text-lg text-gray-900">{shop.name}</span>
          </div>
          <LangSwitcher className="text-gray-500" />
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Hero */}
        <div className="card">
          <div className="flex gap-4">
            {shop.photo_url ? (
              <img src={shop.photo_url} alt={shop.name} className="w-24 h-24 rounded-xl object-cover" />
            ) : (
              <div className="w-24 h-24 rounded-xl bg-brand-100 flex items-center justify-center text-4xl">✂</div>
            )}
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold">{shop.name}</h1>
                <span className={`text-xs font-semibold px-2 py-1 rounded-full ${STATUS_COLORS[shop.status]}`}>
                  {t(`status.${shop.status}`)}
                </span>
              </div>
              {shop.location && <p className="text-gray-500 text-sm mt-1">{shop.location}</p>}
              {shop.description && <p className="text-gray-600 text-sm mt-2">{shop.description}</p>}
            </div>
          </div>
          {shop.status !== "closed" && (
            <div className="mt-4 flex items-baseline gap-1">
              <span className="text-4xl font-bold text-brand-700">{shop.wait_time}</span>
              <span className="text-gray-500">{t("shop_detail.min_estimated_wait")}</span>
            </div>
          )}
        </div>

        {/* Flash Discounts */}
        {discounts.length > 0 && (
          <div>
            <h2 className="font-bold text-lg mb-3">{t("shop_detail.flash_deals")}</h2>
            <div className="space-y-3">
              {discounts.map((d) => <DiscountCard key={d.id} discount={d} />)}
            </div>
          </div>
        )}

        {/* Staff */}
        {employees.length > 0 && (
          <div>
            <h2 className="font-bold text-lg mb-3">{t("shop_detail.staff")}</h2>
            <div className="grid grid-cols-2 gap-3">
              {employees.map((emp) => (
                <div key={emp.id} className="card p-4 text-center">
                  {emp.photo_url ? (
                    <img src={emp.photo_url} alt={emp.name} className="w-16 h-16 rounded-full mx-auto object-cover mb-2" />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-brand-100 mx-auto flex items-center justify-center text-2xl mb-2">👤</div>
                  )}
                  <p className="font-semibold">{emp.name}</p>
                  {emp.role && <p className="text-xs text-gray-500">{emp.role}</p>}
                  <p className="text-brand-700 font-bold mt-1">{emp.wait_time} min</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Price List */}
        {shop.price_list && shop.price_list.length > 0 && (
          <div>
            <h2 className="font-bold text-lg mb-3">{t("shop_detail.prices")}</h2>
            <div className="card divide-y divide-gray-100 p-0">
              {shop.price_list.map((item, i) => (
                <div key={i} className="flex justify-between px-6 py-3">
                  <span>{item.service}</span>
                  <span className="font-semibold">€{item.price}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Opening Hours */}
        {shop.opening_hours && (
          <div>
            <h2 className="font-bold text-lg mb-3">{t("shop_detail.opening_hours")}</h2>
            <div className="card p-0">
              {Object.entries(shop.opening_hours).map(([day, hours]) => (
                <div key={day} className="flex justify-between px-6 py-2.5 border-b last:border-0 border-gray-100">
                  <span className="text-gray-600">{t(`shop_detail.days.${day}`, day)}</span>
                  <span className="font-medium">{hours || t("status.closed")}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reservation */}
        {shop.status !== "closed" && (
          <div>
            <h2 className="font-bold text-lg mb-3">{t("shop_detail.reserve_title")}</h2>
            <div className="card">
              {reservationDone ? (
                <div className="text-center py-4">
                  <div className="text-4xl mb-2">✅</div>
                  <p className="font-semibold text-gray-900">{t("shop_detail.reserved_title")}</p>
                  <p className="text-gray-500 text-sm mt-1">{t("shop_detail.reserved_desc")}</p>
                </div>
              ) : (
                <form onSubmit={(e) => { e.preventDefault(); reserveMutation.mutate(); }} className="space-y-4">
                  <p className="text-sm text-gray-600">{t("shop_detail.reserve_hint")}</p>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("shop_detail.phone_number")}</label>
                    <input className="input" type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+49 123 456789" required />
                  </div>
                  {employees.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">{t("shop_detail.preferred_barber")}</label>
                      <select className="input" value={selectedEmployee ?? ""} onChange={(e) => setSelectedEmployee(e.target.value ? Number(e.target.value) : undefined)}>
                        <option value="">{t("shop_detail.any_barber")}</option>
                        {employees.map((emp) => (
                          <option key={emp.id} value={emp.id}>{emp.name} — {emp.wait_time} min</option>
                        ))}
                      </select>
                    </div>
                  )}
                  {reservationError && <p className="text-sm text-red-600">{reservationError}</p>}
                  <button type="submit" className="btn-primary w-full" disabled={reserveMutation.isPending}>
                    {reserveMutation.isPending ? t("shop_detail.reserving") : t("shop_detail.reserve_btn")}
                  </button>
                  <p className="text-xs text-gray-400 text-center">{t("shop_detail.rate_limit_note")}</p>
                </form>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function DiscountCard({ discount }: { discount: FlashDiscount }) {
  const { t } = useTranslation();
  return (
    <div className="bg-brand-50 border border-brand-200 rounded-xl px-4 py-3 flex items-start gap-3">
      <span className="text-2xl">🏷</span>
      <div>
        <p className="font-semibold text-brand-900">{discount.title}</p>
        {discount.description && <p className="text-sm text-brand-700 mt-0.5">{discount.description}</p>}
        <div className="flex gap-3 mt-1 text-xs text-brand-600">
          {discount.expires_at && <span>{t("shop_detail.expires")} {new Date(discount.expires_at).toLocaleDateString()}</span>}
          {discount.max_uses && <span>{discount.max_uses - discount.uses_count} {t("shop_detail.spots_left")}</span>}
        </div>
      </div>
    </div>
  );
}
