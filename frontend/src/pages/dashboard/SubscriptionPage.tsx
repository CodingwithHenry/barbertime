import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import { shopApi, stripeApi } from "../../api";

type Plan = "monthly" | "yearly";

export default function SubscriptionPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const justSubscribed = searchParams.get("success") === "1";
  const { data: shop } = useQuery({ queryKey: ["me"], queryFn: shopApi.me });
  const statusKey = (shop?.subscription_status ?? "inactive") as keyof typeof statusLabels;
  const [selectedPlan, setSelectedPlan] = useState<Plan>("yearly");

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
    mutationFn: (plan: Plan) => stripeApi.subscribe(plan),
    onSuccess: (data) => { window.location.href = data.url; },
  });

  const portalMutation = useMutation({
    mutationFn: stripeApi.portal,
    onSuccess: (data) => { window.location.href = data.url; },
  });

  const features = t("subscription.features", { returnObjects: true }) as string[];
  const isInactive = statusKey === "inactive" || statusKey === "canceled";

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-2xl font-bold">{t("subscription.title")}</h1>

      {justSubscribed && (
        <div className="bg-green-50 border border-green-200 text-green-800 rounded-lg px-4 py-3 text-sm font-medium">
          🎉 {t("subscription.success")}
        </div>
      )}

      {/* Current status */}
      <div className="card flex items-center gap-3">
        <span className={`text-sm font-semibold px-3 py-1 rounded-full ${color}`}>{label}</span>
        <span className="text-gray-500 text-sm">{desc}</span>
      </div>

      {isInactive ? (
        <>
          {/* Plan selector */}
          <div className="grid grid-cols-2 gap-4">
            {/* Yearly */}
            <button
              onClick={() => setSelectedPlan("yearly")}
              className={`relative rounded-xl border-2 p-5 text-left transition-all ${
                selectedPlan === "yearly"
                  ? "border-brand-600 bg-brand-50"
                  : "border-gray-200 bg-white hover:border-gray-300"
              }`}
            >
              <span className="absolute -top-2.5 left-4 bg-brand-600 text-white text-xs font-semibold px-2 py-0.5 rounded-full">
                {t("subscription.most_popular")}
              </span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-3xl font-bold">{t("subscription.yearly_price")}</span>
                <span className="text-gray-400 text-sm">{t("subscription.per_month")}</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">{t("subscription.billed_yearly")}</p>
              <p className="text-xs font-medium text-brand-700 mt-1">{t("subscription.yearly_total")}</p>
            </button>

            {/* Monthly */}
            <button
              onClick={() => setSelectedPlan("monthly")}
              className={`rounded-xl border-2 p-5 text-left transition-all ${
                selectedPlan === "monthly"
                  ? "border-brand-600 bg-brand-50"
                  : "border-gray-200 bg-white hover:border-gray-300"
              }`}
            >
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-3xl font-bold">{t("subscription.monthly_price")}</span>
                <span className="text-gray-400 text-sm">{t("subscription.per_month")}</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">{t("subscription.billed_monthly")}</p>
            </button>
          </div>

          {/* Features */}
          <ul className="space-y-1.5 text-sm text-gray-600">
            {features.map((feature) => (
              <li key={feature} className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                {feature}
              </li>
            ))}
          </ul>

          <button
            onClick={() => subscribeMutation.mutate(selectedPlan)}
            className="btn-primary w-full"
            disabled={subscribeMutation.isPending}
          >
            {subscribeMutation.isPending
              ? t("subscription.redirecting")
              : selectedPlan === "yearly"
              ? t("subscription.subscribe_yearly")
              : t("subscription.subscribe_monthly")}
          </button>

          {subscribeMutation.isError && (
            <p className="text-sm text-red-600">{(subscribeMutation.error as Error).message}</p>
          )}
        </>
      ) : (
        <button
          onClick={() => portalMutation.mutate()}
          className="btn-secondary w-full"
          disabled={portalMutation.isPending}
        >
          {portalMutation.isPending ? t("common.loading") : t("subscription.manage_btn")}
        </button>
      )}
    </div>
  );
}
