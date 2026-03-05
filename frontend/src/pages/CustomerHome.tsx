import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { publicApi, type Shop } from "../api";
import LangSwitcher from "../components/LangSwitcher";

export default function CustomerHome() {
  const { t } = useTranslation();
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);

  useEffect(() => {
    navigator.geolocation?.getCurrentPosition(
      (pos) => setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => {}
    );
  }, []);

  const { data: shops = [], isLoading } = useQuery({
    queryKey: ["public-shops", coords],
    queryFn: () => publicApi.listShops(coords?.lat, coords?.lon),
  });

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <span className="text-2xl font-bold text-brand-700">✂ BarberTime</span>
          <div className="flex items-center gap-4">
            <LangSwitcher className="text-gray-500" />
            <Link to="/dashboard" className="text-sm text-brand-600 hover:underline font-medium">
              {t("customer.for_barbers")}
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{t("customer.find_barber")}</h1>
          <p className="text-gray-500 mt-1">{t("customer.tagline")}</p>
          {coords && (
            <p className="text-xs text-gray-400 mt-1">{t("customer.sorted_by_distance")}</p>
          )}
        </div>

        {isLoading && (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card animate-pulse h-28" />
            ))}
          </div>
        )}

        {!isLoading && shops.length === 0 && (
          <div className="text-center py-20 text-gray-400">
            <p className="text-5xl mb-4">✂</p>
            <p className="text-lg">{t("customer.no_shops")}</p>
          </div>
        )}

        <div className="space-y-4">
          {shops.map((shop) => (
            <ShopCard key={shop.id} shop={shop} />
          ))}
        </div>
      </main>
    </div>
  );
}

function ShopCard({ shop }: { shop: Shop }) {
  const { t } = useTranslation();

  const STATUS_COLORS = {
    open: "bg-green-100 text-green-800",
    busy: "bg-yellow-100 text-yellow-800",
    closed: "bg-gray-100 text-gray-600",
  };

  return (
    <Link to={`/shops/${shop.slug}`} className="block">
      <div className="card hover:shadow-md transition-shadow cursor-pointer flex gap-4">
        {shop.photo_url ? (
          <img src={shop.photo_url} alt={shop.name} className="w-20 h-20 rounded-lg object-cover flex-shrink-0" />
        ) : (
          <div className="w-20 h-20 rounded-lg bg-brand-100 flex items-center justify-center flex-shrink-0 text-3xl">✂</div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h2 className="font-bold text-lg text-gray-900 truncate">{shop.name}</h2>
            <span className={`text-xs font-semibold px-2 py-1 rounded-full flex-shrink-0 ${STATUS_COLORS[shop.status]}`}>
              {t(`status.${shop.status}`)}
            </span>
          </div>
          {shop.location && <p className="text-sm text-gray-500 mt-0.5 truncate">{shop.location}</p>}
          <div className="mt-2 flex items-center gap-1">
            {shop.status !== "closed" ? (
              <>
                <span className="text-2xl font-bold text-brand-700">{shop.wait_time}</span>
                <span className="text-gray-500 text-sm">{t("customer.min_wait")}</span>
              </>
            ) : (
              <span className="text-gray-400 text-sm">{t("customer.currently_closed")}</span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
