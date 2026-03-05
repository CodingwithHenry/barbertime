import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { authApi } from "../../api";
import LangSwitcher from "../../components/LangSwitcher";

export default function Login() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const justReset = searchParams.get("reset") === "1";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { access_token } = await authApi.login(email, password);
      localStorage.setItem("token", access_token);
      navigate("/dashboard");
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
          <p className="text-gray-500 mt-1">{t("auth.barber_dashboard")}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-xl font-bold">{t("auth.sign_in")}</h1>
            <LangSwitcher className="text-gray-400" />
          </div>
          {justReset && (
            <p className="text-sm text-green-600 mb-4">{t("auth.reset_success")}</p>
          )}
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t("common.email")}</label>
              <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t("common.password")}</label>
              <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? t("auth.signing_in") : t("auth.sign_in_btn")}
            </button>
          </form>
          <div className="flex justify-between text-sm text-gray-500 mt-4">
            <span>{t("auth.no_account")}{" "}
              <Link to="/dashboard/register" className="text-brand-600 hover:underline">{t("auth.register_link")}</Link>
            </span>
            <Link to="/forgot-password" className="text-brand-600 hover:underline">{t("auth.forgot_password")}</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
