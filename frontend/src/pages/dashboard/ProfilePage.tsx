import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { shopApi, type Shop } from "../../api";

const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
const DAY_KEYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function ProfilePage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: shop } = useQuery({ queryKey: ["me"], queryFn: shopApi.me });
  const fileRef = useRef<HTMLInputElement>(null);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    name: shop?.name ?? "",
    location: shop?.location ?? "",
    latitude: shop?.latitude?.toString() ?? "",
    longitude: shop?.longitude?.toString() ?? "",
    description: shop?.description ?? "",
    opening_hours: shop?.opening_hours ?? {} as Record<string, string>,
    price_list: (shop?.price_list ?? []) as { service: string; price: number }[],
  });

  useEffect(() => {
    if (shop) {
      setForm({
        name: shop.name,
        location: shop.location ?? "",
        latitude: shop.latitude?.toString() ?? "",
        longitude: shop.longitude?.toString() ?? "",
        description: shop.description ?? "",
        opening_hours: shop.opening_hours ?? {},
        price_list: (shop.price_list ?? []) as { service: string; price: number }[],
      });
    }
  }, [shop?.id]);

  const updateMutation = useMutation({
    mutationFn: () =>
      shopApi.updateProfile({
        name: form.name,
        location: form.location || undefined,
        latitude: form.latitude ? parseFloat(form.latitude) : undefined,
        longitude: form.longitude ? parseFloat(form.longitude) : undefined,
        description: form.description || undefined,
        opening_hours: form.opening_hours,
        price_list: form.price_list,
      }),
    onSuccess: (updated) => {
      qc.setQueryData(["me"], updated);
      setSaved(true);
      setError("");
      setTimeout(() => setSaved(false), 2000);
    },
    onError: (e: Error) => setError(e.message),
  });

  const photoMutation = useMutation({
    mutationFn: (file: File) => shopApi.uploadPhoto(file),
    onSuccess: (updated) => qc.setQueryData(["me"], updated),
  });

  function updateHours(day: string, value: string) {
    setForm((f) => ({ ...f, opening_hours: { ...f.opening_hours, [day]: value } }));
  }

  function addPriceItem() {
    setForm((f) => ({ ...f, price_list: [...f.price_list, { service: "", price: 0 }] }));
  }

  function updatePriceItem(i: number, field: "service" | "price", value: string) {
    setForm((f) => {
      const list = [...f.price_list];
      list[i] = { ...list[i], [field]: field === "price" ? parseFloat(value) || 0 : value };
      return { ...f, price_list: list };
    });
  }

  function removePriceItem(i: number) {
    setForm((f) => ({ ...f, price_list: f.price_list.filter((_, idx) => idx !== i) }));
  }

  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-2xl font-bold">{t("profile.title")}</h1>

      <div className="card flex items-center gap-4">
        {shop?.photo_url ? (
          <img src={shop.photo_url} alt="Shop" className="w-20 h-20 rounded-xl object-cover" />
        ) : (
          <div className="w-20 h-20 rounded-xl bg-brand-100 flex items-center justify-center text-3xl">✂</div>
        )}
        <div>
          <p className="font-medium">{t("profile.shop_photo")}</p>
          <button onClick={() => fileRef.current?.click()} className="btn-secondary text-sm mt-1" disabled={photoMutation.isPending}>
            {photoMutation.isPending ? t("common.uploading") : t("common.upload_photo")}
          </button>
          <input ref={fileRef} type="file" accept="image/*" className="hidden"
            onChange={(e) => e.target.files?.[0] && photoMutation.mutate(e.target.files[0])} />
        </div>
      </div>

      <div className="card space-y-4">
        <h2 className="font-semibold text-lg">{t("profile.basic_info")}</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t("profile.shop_name")}</label>
          <input className="input" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t("profile.location")}</label>
          <input className="input" value={form.location} onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))} placeholder="Musterstraße 1, Berlin" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t("profile.latitude")}</label>
            <input className="input" type="number" step="any" value={form.latitude} onChange={(e) => setForm((f) => ({ ...f, latitude: e.target.value }))} placeholder="52.520" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t("profile.longitude")}</label>
            <input className="input" type="number" step="any" value={form.longitude} onChange={(e) => setForm((f) => ({ ...f, longitude: e.target.value }))} placeholder="13.405" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t("profile.description")}</label>
          <textarea className="input resize-none" rows={3} value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            placeholder={t("profile.description_placeholder")} />
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="font-semibold text-lg">{t("profile.opening_hours")}</h2>
        {DAYS.map((day, i) => (
          <div key={day} className="flex items-center gap-3">
            <span className="w-24 text-sm text-gray-600">{t(`profile.days.${DAY_KEYS[i]}`)}</span>
            <input className="input" value={form.opening_hours[day] ?? ""} onChange={(e) => updateHours(day, e.target.value)} placeholder="9:00–18:00" />
          </div>
        ))}
      </div>

      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-lg">{t("profile.price_list")}</h2>
          <button onClick={addPriceItem} className="text-sm text-brand-600 hover:underline">+ {t("common.add")}</button>
        </div>
        {form.price_list.map((item, i) => (
          <div key={i} className="flex gap-2 items-center">
            <input className="input flex-1" value={item.service} onChange={(e) => updatePriceItem(i, "service", e.target.value)} placeholder={t("profile.service_name")} />
            <div className="relative w-28">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">€</span>
              <input className="input pl-7" type="number" min="0" step="0.5" value={item.price} onChange={(e) => updatePriceItem(i, "price", e.target.value)} />
            </div>
            <button onClick={() => removePriceItem(i)} className="text-gray-400 hover:text-red-500 text-xl leading-none">×</button>
          </div>
        ))}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      <button onClick={() => updateMutation.mutate()} className="btn-primary w-full" disabled={updateMutation.isPending}>
        {updateMutation.isPending ? t("common.saving") : saved ? t("common.saved") : t("profile.save_btn")}
      </button>
    </div>
  );
}
