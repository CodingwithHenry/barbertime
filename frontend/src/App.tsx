import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import CustomerHome from "./pages/CustomerHome";
import ShopDetail from "./pages/ShopDetail";
import DashboardLayout from "./pages/dashboard/DashboardLayout";
import Login from "./pages/dashboard/Login";
import Register from "./pages/dashboard/Register";
import DashboardHome from "./pages/dashboard/DashboardHome";
import ProfilePage from "./pages/dashboard/ProfilePage";
import EmployeesPage from "./pages/dashboard/EmployeesPage";
import DiscountsPage from "./pages/dashboard/DiscountsPage";
import SubscriptionPage from "./pages/dashboard/SubscriptionPage";
import ReservationsPage from "./pages/dashboard/ReservationsPage";
import SharePage from "./pages/dashboard/SharePage";
import VerifyEmailPage from "./pages/dashboard/VerifyEmailPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import EmbedWidget from "./pages/EmbedWidget";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("token");
  if (!token) return <Navigate to="/dashboard/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Customer-facing */}
        <Route path="/" element={<CustomerHome />} />
        <Route path="/shops/:slug" element={<ShopDetail />} />
        <Route path="/embed/shops/:slug" element={<EmbedWidget />} />

        {/* Auth */}
        <Route path="/dashboard/login" element={<Login />} />
        <Route path="/dashboard/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Protected dashboard */}
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <DashboardLayout />
            </RequireAuth>
          }
        >
          <Route index element={<DashboardHome />} />
          <Route path="verify-email" element={<VerifyEmailPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="employees" element={<EmployeesPage />} />
          <Route path="discounts" element={<DiscountsPage />} />
          <Route path="reservations" element={<ReservationsPage />} />
          <Route path="share" element={<SharePage />} />
          <Route path="subscription" element={<SubscriptionPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
