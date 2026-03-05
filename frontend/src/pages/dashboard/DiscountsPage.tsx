import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { discountApi, type FlashDiscount } from "../../api";

export default function DiscountsPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: discounts = [] } = useQuery({ queryKey: ["discounts"], queryFn: discountApi.list });
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", expires_at: "", max_uses: "" });

  const createMutation = useMutation({
    mutationFn: () =>
      discountApi.create({
        title: form.title,
        description: form.description || undefined,
        expires_at: form.expires_at || undefined,
        max_uses: form.max_uses ? parseInt(form.max_uses) : undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["discounts"] });
      setForm({ title: "", description: "", expires_at: "", max_uses: "" });
      setAdding(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => discountApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["discounts"] }),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => discountApi.update(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["discounts"] }),
  });

  const redeemMutation = useMutation({
    mutationFn: (id: number) => discountApi.redeem(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["discounts"] }),
  });

  return (
    <div className="max-w-lg space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("discounts.title")}</h1>
        <button onClick={() => setAdding(true)} className="btn-primary text-sm">{t("discounts.new_btn")}</button>
      </div>

      {adding && (
        <div className="card space-y-4">
          <h2 className="font-semibold">{t("discounts.new_title")}</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t("discounts.deal_title")}</label>
            <input className="input" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t("discounts.description")}</label>
            <textarea className="input resize-none" rows={2} value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t("discounts.expires_at")}</label>
              <input className="input" type="datetime-local" value={form.expires_at}
                onChange={(e) => setForm((f) => ({ ...f, expires_at: e.target.value }))} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t("discounts.max_uses")}</label>
              <input className="input" type="number" min="1" value={form.max_uses}
                onChange={(e) => setForm((f) => ({ ...f, max_uses: e.target.value }))} placeholder="2" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => createMutation.mutate()} className="btn-primary" disabled={!form.title || createMutation.isPending}>
              {createMutation.isPending ? t("discounts.creating") : t("discounts.create_btn")}
            </button>
            <button onClick={() => setAdding(false)} className="btn-secondary">{t("common.cancel")}</button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {discounts.map((d) => (
          <div key={d.id} className="card">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="font-semibold">{d.title}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${d.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                    {d.is_active ? t("discounts.active") : t("discounts.inactive")}
                  </span>
                </div>
                {d.description && <p className="text-sm text-gray-500 mt-0.5">{d.description}</p>}
                <div className="flex gap-3 mt-1 text-xs text-gray-400">
                  {d.max_uses != null && (
                  <span className={d.uses_count >= d.max_uses ? "text-red-500 font-medium" : ""}>
                    {d.uses_count >= d.max_uses
                      ? t("discounts.exhausted")
                      : t("discounts.remaining", { count: d.max_uses - d.uses_count })}
                    {" "}({d.uses_count}/{d.max_uses})
                  </span>
                )}
                  {d.expires_at && <span>{t("discounts.until")} {new Date(d.expires_at).toLocaleString()}</span>}
                </div>
              </div>
              <div className="flex gap-2 flex-wrap justify-end">
                {d.is_active && (d.max_uses == null || d.uses_count < d.max_uses) && (
                  <button
                    onClick={() => redeemMutation.mutate(d.id)}
                    disabled={redeemMutation.isPending}
                    className="text-xs px-3 py-1 bg-brand-100 text-brand-700 hover:bg-brand-200 rounded-lg font-medium"
                  >
                    {redeemMutation.isPending ? t("discounts.redeeming") : t("discounts.redeem")}
                  </button>
                )}
                <button onClick={() => toggleMutation.mutate({ id: d.id, is_active: !d.is_active })} className="text-xs btn-secondary py-1">
                  {d.is_active ? t("discounts.pause") : t("discounts.resume")}
                </button>
                <button onClick={() => deleteMutation.mutate(d.id)} className="text-gray-300 hover:text-red-500 text-xl leading-none">×</button>
              </div>
            </div>
          </div>
        ))}
        {discounts.length === 0 && !adding && (
          <div className="text-center py-12 text-gray-400">
            <p className="text-4xl mb-2">🏷</p>
            <p>{t("discounts.no_deals")}</p>
          </div>
        )}
      </div>
    </div>
  );
}
