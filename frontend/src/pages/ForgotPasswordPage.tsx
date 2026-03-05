import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { authApi } from "../api";
import LangSwitcher from "../components/LangSwitcher";

export default function ForgotPasswordPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      setSent(true);
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
            <h1 className="text-xl font-bold">{t("auth.forgot_title")}</h1>
            <LangSwitcher className="text-gray-400" />
          </div>
          {sent ? (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">{t("auth.forgot_sent")}</p>
              <Link
                to={`/reset-password?email=${encodeURIComponent(email)}`}
                className="btn-primary w-full block text-center"
              >
                {t("auth.enter_code")}
              </Link>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              <p className="text-sm text-gray-500">{t("auth.forgot_desc")}</p>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t("common.email")}</label>
                <input
                  className="input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn-primary w-full" disabled={loading}>
                {loading ? t("auth.sending_code") : t("auth.send_code_btn")}
              </button>
            </form>
          )}
          <p className="text-center text-sm text-gray-500 mt-4">
            <Link to="/dashboard/login" className="text-brand-600 hover:underline">{t("auth.back_to_login")}</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
