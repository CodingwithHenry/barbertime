import { Outlet, NavLink, Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import LangSwitcher from "../../components/LangSwitcher";
import { shopApi } from "../../api";

export default function DashboardLayout() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data: shop } = useQuery({ queryKey: ["me"], queryFn: shopApi.me });

  const NAV = [
    { to: "/dashboard", label: t("nav.status"), icon: "⚡", end: true },
    { to: "/dashboard/profile", label: t("nav.profile"), icon: "🏪" },
    { to: "/dashboard/employees", label: t("nav.staff"), icon: "👥" },
    { to: "/dashboard/reservations", label: t("nav.queue"), icon: "📋" },
    { to: "/dashboard/discounts", label: t("nav.deals"), icon: "🏷" },
    { to: "/dashboard/share", label: t("nav.share"), icon: "🔗" },
    { to: "/dashboard/subscription", label: t("nav.plan"), icon: "💳" },
  ];

  function logout() {
    localStorage.removeItem("token");
    navigate("/dashboard/login");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-brand-700 text-white">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <span className="font-bold text-lg">✂ BarberTime</span>
          <div className="flex items-center gap-4">
            <LangSwitcher className="text-brand-200" />
            <button onClick={logout} className="text-sm text-brand-200 hover:text-white">
              {t("nav.logout")}
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 max-w-5xl mx-auto w-full">
        <nav className="hidden md:flex flex-col w-52 border-r border-gray-200 bg-white pt-6 px-3 gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? "bg-brand-100 text-brand-700" : "text-gray-600 hover:bg-gray-100"
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex z-10">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex-1 flex flex-col items-center py-2 text-xs font-medium transition-colors ${
                  isActive ? "text-brand-700" : "text-gray-500"
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <main className="flex-1 p-6 pb-24 md:pb-6 overflow-auto">
          {shop && !shop.is_verified && (
            <div className="mb-5 bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 flex items-center justify-between text-sm">
              <span className="text-yellow-800">{t("auth.verify_banner")}</span>
              <Link to="/dashboard/verify-email" className="text-yellow-700 font-semibold hover:underline shrink-0 ml-3">
                {t("auth.verify_now")}
              </Link>
            </div>
          )}
          <Outlet />
        </main>
      </div>
    </div>
  );
}
