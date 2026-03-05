import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { authApi, shopApi } from "../../api";

export default function VerifyEmailPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data: shop } = useQuery({ queryKey: ["me"], queryFn: shopApi.me });
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resent, setResent] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.verifyEmail(code);
      await qc.invalidateQueries({ queryKey: ["me"] });
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function resend() {
    try {
      await authApi.resendVerification();
      setResent(true);
      setTimeout(() => setResent(false), 4000);
    } catch {}
  }

  return (
    <div className="max-w-sm mx-auto space-y-6 pt-4">
      <div>
        <h1 className="text-2xl font-bold">{t("auth.verify_email_title")}</h1>
        <p className="text-gray-500 text-sm mt-1">
          {t("auth.verify_email_desc", { email: shop?.email ?? "" })}
        </p>
      </div>
      <div className="card">
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t("auth.code_label")}</label>
            <input
              className="input text-2xl tracking-widest text-center font-mono"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              maxLength={6}
              placeholder="000000"
              required
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" className="btn-primary w-full" disabled={loading || code.length !== 6}>
            {loading ? t("auth.verifying") : t("auth.verify_btn")}
          </button>
        </form>
        <button onClick={resend} className="mt-3 text-sm text-brand-600 hover:underline w-full text-center">
          {resent ? t("auth.resent") : t("auth.resend_code")}
        </button>
      </div>
    </div>
  );
}
