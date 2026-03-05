import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { employeeApi, shopApi, type Employee } from "../../api";

export default function EmployeesPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: employees = [] } = useQuery({ queryKey: ["employees"], queryFn: employeeApi.list });
  const { data: shop } = useQuery({ queryKey: ["me"], queryFn: shopApi.me });

  const [newName, setNewName] = useState("");
  const [newRole, setNewRole] = useState("");
  const [adding, setAdding] = useState(false);

  const createMutation = useMutation({
    mutationFn: () => employeeApi.create(newName, newRole || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["employees"] });
      setNewName("");
      setNewRole("");
      setAdding(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => employeeApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["employees"] }),
  });

  return (
    <div className="max-w-lg space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("employees.title")}</h1>
        <button onClick={() => setAdding(true)} className="btn-primary text-sm">{t("employees.add_btn")}</button>
      </div>

      {adding && (
        <div className="card space-y-3">
          <h2 className="font-semibold">{t("employees.new_member")}</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t("common.name")}</label>
            <input className="input" value={newName} onChange={(e) => setNewName(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t("nav.staff")} ({t("common.optional")})</label>
            <input className="input" value={newRole} onChange={(e) => setNewRole(e.target.value)} placeholder={t("employees.role_placeholder")} />
          </div>
          <div className="flex gap-2">
            <button onClick={() => createMutation.mutate()} className="btn-primary" disabled={!newName || createMutation.isPending}>
              {createMutation.isPending ? t("common.adding") : t("common.add")}
            </button>
            <button onClick={() => setAdding(false)} className="btn-secondary">{t("common.cancel")}</button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {employees.map((emp) => (
          <EmployeeCard key={emp.id} employee={emp} onDelete={() => deleteMutation.mutate(emp.id)} />
        ))}
        {employees.length === 0 && !adding && (
          <div className="text-center py-12 text-gray-400">
            <p className="text-4xl mb-2">👥</p>
            <p>{t("employees.no_staff")}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function EmployeeCard({ employee, onDelete }: { employee: Employee; onDelete: () => void }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [waitTime, setWaitTime] = useState(employee.wait_time);
  const [saved, setSaved] = useState(false);

  const { data: suggestion } = useQuery({
    queryKey: ["suggest-wait-emp", employee.id],
    queryFn: () => employeeApi.suggestWait(employee.id),
  });

  const updateMutation = useMutation({
    mutationFn: () => employeeApi.update(employee.id, { wait_time: waitTime }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["employees"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (is_active: boolean) => employeeApi.update(employee.id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["employees"] }),
  });

  const photoMutation = useMutation({
    mutationFn: (file: File) => employeeApi.uploadPhoto(employee.id, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["employees"] }),
  });

  return (
    <div className={`card space-y-4 ${!employee.is_active ? "opacity-60" : ""}`}>
      <div className="flex items-center gap-3">
        <div className="relative">
          {employee.photo_url ? (
            <img src={employee.photo_url} alt={employee.name} className="w-14 h-14 rounded-full object-cover" />
          ) : (
            <div className="w-14 h-14 rounded-full bg-brand-100 flex items-center justify-center text-2xl">👤</div>
          )}
          <button
            onClick={() => fileRef.current?.click()}
            className="absolute -bottom-1 -right-1 w-6 h-6 bg-white border border-gray-300 rounded-full flex items-center justify-center text-xs hover:bg-gray-50"
          >
            📷
          </button>
          <input ref={fileRef} type="file" accept="image/*" className="hidden"
            onChange={(e) => e.target.files?.[0] && photoMutation.mutate(e.target.files[0])} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <p className="font-semibold">{employee.name}</p>
            {!employee.is_active && (
              <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{t("employees.away_badge")}</span>
            )}
          </div>
          {employee.role && <p className="text-sm text-gray-500">{employee.role}</p>}
        </div>
        <button
          onClick={() => toggleActiveMutation.mutate(!employee.is_active)}
          disabled={toggleActiveMutation.isPending}
          className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
            employee.is_active
              ? "bg-gray-100 text-gray-600 hover:bg-yellow-100 hover:text-yellow-700"
              : "bg-green-100 text-green-700 hover:bg-green-200"
          }`}
        >
          {employee.is_active ? t("employees.set_away") : t("employees.set_available")}
        </button>
        <button onClick={onDelete} className="text-gray-300 hover:text-red-500 text-xl">×</button>
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-sm font-medium text-gray-700">{t("employees.wait_time")}</label>
          {suggestion?.suggested_wait_time != null && (
            <button className="text-xs text-brand-600 hover:underline" onClick={() => setWaitTime(suggestion.suggested_wait_time!)}>
              {t("employees.suggestion", { minutes: suggestion.suggested_wait_time })}
            </button>
          )}
        </div>
        <div className="flex items-center gap-3">
          <input type="range" min={0} max={90} step={5} value={waitTime}
            onChange={(e) => setWaitTime(Number(e.target.value))} className="flex-1 accent-brand-600" />
          <span className="text-lg font-bold text-brand-700 w-14 text-right">{waitTime} min</span>
        </div>
        <button onClick={() => updateMutation.mutate()} className="btn-secondary text-sm mt-2" disabled={updateMutation.isPending}>
          {updateMutation.isPending ? t("common.saving") : saved ? t("common.saved") : t("employees.save_wait")}
        </button>
      </div>
    </div>
  );
}
