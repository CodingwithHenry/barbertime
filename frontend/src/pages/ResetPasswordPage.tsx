import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { authApi } from "../api";
import LangSwitcher from "../components/LangSwitcher";

export default function ResetPasswordPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const email = searchParams.get("email") ?? "";
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.resetPassword(email, code, password);
      navigate("/dashboard/login?reset=1");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link to="/" className="text-3xl font-bold text-brand-700">✂ BarberTime</Link>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-xl font-bold">{t("auth.reset_title")}</h1>
            <LangSwitcher className="text-gray-400" />
          </div>
          <form onSubmit={submit} className="space-y-4">
            <p className="text-sm text-gray-500">{t("auth.reset_desc")}</p>
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t("auth.new_password")}</label>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button type="submit" className="btn-primary w-full" disabled={loading || code.length !== 6}>
              {loading ? t("auth.resetting") : t("auth.reset_btn")}
            </button>
          </form>
          <p className="text-center text-sm text-gray-500 mt-4">
            <Link to="/dashboard/login" className="text-brand-600 hover:underline">{t("auth.back_to_login")}</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
