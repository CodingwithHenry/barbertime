import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { shopApi, type Shop } from "../../api";

export default function DashboardHome() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: shop } = useQuery({ queryKey: ["me"], queryFn: shopApi.me });

  const [status, setStatus] = useState<Shop["status"]>(shop?.status ?? "closed");
  const [waitTime, setWaitTime] = useState(shop?.wait_time ?? 0);
  const [saved, setSaved] = useState(false);

  const { data: suggestion } = useQuery({
    queryKey: ["suggest-wait"],
    queryFn: () => shopApi.suggestWaitTime(),
    enabled: !!shop,
  });

  const updateMutation = useMutation({
    mutationFn: () => shopApi.updateStatus(status, waitTime),
    onSuccess: (updated) => {
      qc.setQueryData(["me"], updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  useEffect(() => {
    if (shop) {
      setStatus(shop.status);
      setWaitTime(shop.wait_time);
    }
  }, [shop?.id]);

  const STATUS_OPTIONS: { value: Shop["status"]; color: string }[] = [
    { value: "open", color: "bg-green-500" },
    { value: "busy", color: "bg-yellow-500" },
    { value: "closed", color: "bg-gray-400" },
  ];

  return (
    <div className="max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t("dashboard_home.title")}</h1>
        {shop && (
          <p className="text-gray-500 text-sm mt-1">
            {t("dashboard_home.shop_visible_at")}{" "}
            <a href={`/shops/${shop.slug}`} target="_blank" className="text-brand-600 hover:underline">
              /shops/{shop.slug}
            </a>
          </p>
        )}
      </div>

      <div className="card space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">{t("dashboard_home.shop_status")}</label>
          <div className="flex gap-2">
            {STATUS_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setStatus(opt.value)}
                className={`flex-1 py-3 rounded-lg font-semibold text-sm border-2 transition-all ${
                  status === opt.value
                    ? "border-brand-600 bg-brand-50 text-brand-700"
                    : "border-gray-200 text-gray-600 hover:border-gray-300"
                }`}
              >
                <span className={`inline-block w-2 h-2 rounded-full mr-2 ${opt.color}`} />
                {t(`status.${opt.value}`)}
              </button>
            ))}
          </div>
        </div>

        {status !== "closed" && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">{t("dashboard_home.wait_time")}</label>
              {suggestion?.suggested_wait_time != null && (
                <button
                  className="text-xs text-brand-600 hover:underline"
                  onClick={() => setWaitTime(suggestion.suggested_wait_time!)}
                >
                  {t("dashboard_home.use_suggestion", { minutes: suggestion.suggested_wait_time })}
                </button>
              )}
            </div>
            <div className="flex items-center gap-3">
              <input
                type="range" min={0} max={90} step={5} value={waitTime}
                onChange={(e) => setWaitTime(Number(e.target.value))}
                className="flex-1 accent-brand-600"
              />
              <span className="text-2xl font-bold text-brand-700 w-16 text-right">{waitTime} min</span>
            </div>
          </div>
        )}

        <button onClick={() => updateMutation.mutate()} className="btn-primary w-full" disabled={updateMutation.isPending}>
          {updateMutation.isPending ? t("common.saving") : saved ? t("common.saved") : t("dashboard_home.update_btn")}
        </button>
      </div>

      {shop && (
        <div className="card bg-gray-50">
          <p className="text-sm text-gray-500">{t("dashboard_home.currently_showing")}</p>
          <div className="flex items-center gap-2 mt-2">
            <span className={`w-3 h-3 rounded-full ${shop.status === "open" ? "bg-green-500" : shop.status === "busy" ? "bg-yellow-500" : "bg-gray-400"}`} />
            <span className="font-semibold">{t(`status.${shop.status}`)}</span>
            {shop.status !== "closed" && (
              <span className="text-gray-500">— {shop.wait_time} min {t("dashboard_home.min_wait")}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
