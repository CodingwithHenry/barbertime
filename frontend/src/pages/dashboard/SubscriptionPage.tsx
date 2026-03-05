import { useQuery, useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import { shopApi, stripeApi } from "../../api";

export default function SubscriptionPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const justSubscribed = searchParams.get("success") === "1";
  const { data: shop } = useQuery({ queryKey: ["me"], queryFn: shopApi.me });
  const statusKey = (shop?.subscription_status ?? "inactive") as keyof typeof statusLabels;

  const statusLabels = {
    active: t("subscription.status.active"),
    trialing: t("subscription.status.trialing"),
    past_due: t("subscription.status.past_due"),
    inactive: t("subscription.status.inactive"),
    canceled: t("subscription.status.canceled"),
  };

  const statusDescs = {
    active: t("subscription.status_desc.active"),
    trialing: t("subscription.status_desc.trialing"),
    past_due: t("subscription.status_desc.past_due"),
    inactive: t("subscription.status_desc.inactive"),
    canceled: t("subscription.status_desc.canceled"),
  };

  const statusColors = {
    active: "text-green-600 bg-green-50",
    trialing: "text-blue-600 bg-blue-50",
    past_due: "text-red-600 bg-red-50",
    inactive: "text-gray-600 bg-gray-100",
    canceled: "text-gray-600 bg-gray-100",
  };

  const label = statusLabels[statusKey] ?? statusLabels.inactive;
  const desc = statusDescs[statusKey] ?? statusDescs.inactive;
  const color = statusColors[statusKey] ?? statusColors.inactive;

  const subscribeMutation = useMutation({
    mutationFn: stripeApi.subscribe,
    onSuccess: (data) => { window.location.href = data.url; },
  });

  const portalMutation = useMutation({
    mutationFn: stripeApi.portal,
    onSuccess: (data) => { window.location.href = data.url; },
  });

  const features = t("subscription.features", { returnObjects: true }) as string[];

  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-2xl font-bold">{t("subscription.title")}</h1>

      {justSubscribed && (
        <div className="bg-green-50 border border-green-200 text-green-800 rounded-lg px-4 py-3 text-sm font-medium">
          🎉 {t("subscription.success")}
        </div>
      )}

      <div className="card space-y-4">
        <div className="flex items-center gap-3">
          <span className={`text-sm font-semibold px-3 py-1 rounded-full ${color}`}>{label}</span>
          <span className="text-gray-500 text-sm">{desc}</span>
        </div>

        <div className="border-t border-gray-100 pt-4">
          <div className="flex items-baseline gap-1">
            <span className="text-4xl font-bold">€15</span>
            <span className="text-gray-400">{t("subscription.per_month")}</span>
          </div>
          <ul className="mt-3 space-y-1.5 text-sm text-gray-600">
            {features.map((feature) => (
              <li key={feature} className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                {feature}
              </li>
            ))}
          </ul>
        </div>

        {statusKey === "inactive" || statusKey === "canceled" ? (
          <button onClick={() => subscribeMutation.mutate()} className="btn-primary w-full" disabled={subscribeMutation.isPending}>
            {subscribeMutation.isPending ? t("subscription.redirecting") : t("subscription.subscribe_btn")}
          </button>
        ) : (
          <button onClick={() => portalMutation.mutate()} className="btn-secondary w-full" disabled={portalMutation.isPending}>
            {portalMutation.isPending ? t("common.loading") : t("subscription.manage_btn")}
          </button>
        )}

        {subscribeMutation.isError && (
          <p className="text-sm text-red-600">{(subscribeMutation.error as Error).message}</p>
        )}
      </div>
    </div>
  );
}
