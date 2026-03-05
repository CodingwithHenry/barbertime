import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { reservationApi, employeeApi, type Reservation } from "../../api";

export default function ReservationsPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: reservations = [], isLoading } = useQuery({
    queryKey: ["reservations"],
    queryFn: reservationApi.list,
    refetchInterval: 30_000,
  });
  const { data: employees = [] } = useQuery({ queryKey: ["employees"], queryFn: employeeApi.list });

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => reservationApi.updateStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reservations"] }),
  });

  function getEmployeeName(id?: number) {
    if (!id) return t("reservations.any_barber");
    return employees.find((e) => e.id === id)?.name ?? t("reservations.any_barber");
  }

  function formatExpiry(expires_at: string) {
    const diff = Math.round((new Date(expires_at).getTime() - Date.now()) / 60000);
    if (diff < 0) return t("reservations.expired");
    if (diff === 0) return t("reservations.less_than_1");
    return t("reservations.min_left", { count: diff });
  }

  return (
    <div className="max-w-lg space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("reservations.title")}</h1>
        <span className="text-sm text-gray-500">{t("reservations.active_count", { count: reservations.length })}</span>
      </div>

      {isLoading && <div className="text-gray-400 text-center py-8">{t("common.loading")}</div>}

      {!isLoading && reservations.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-4xl mb-2">📋</p>
          <p>{t("reservations.no_reservations")}</p>
        </div>
      )}

      <div className="space-y-3">
        {reservations.map((res, i) => (
          <div key={res.id} className="card flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 font-bold flex items-center justify-center flex-shrink-0">
              {i + 1}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{getEmployeeName(res.employee_id)}</p>
              <p className="text-xs text-gray-400">{formatExpiry(res.expires_at)}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => updateMutation.mutate({ id: res.id, status: "honoured" })}
                className="text-xs px-3 py-1.5 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 font-medium">
                {t("reservations.done")}
              </button>
              <button onClick={() => updateMutation.mutate({ id: res.id, status: "cancelled" })}
                className="text-xs px-3 py-1.5 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 font-medium">
                {t("reservations.no_show")}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
