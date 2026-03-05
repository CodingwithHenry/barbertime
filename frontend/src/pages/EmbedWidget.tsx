import { useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { publicApi, type Shop } from "../api";

export default function EmbedWidget() {
  const { slug } = useParams<{ slug: string }>();
  const { t } = useTranslation();
  const qc = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);

  const { data: shop, isLoading } = useQuery({
    queryKey: ["embed-shop", slug],
    queryFn: () => publicApi.getShop(slug!),
    enabled: !!slug,
  });

  useEffect(() => {
    if (!shop) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/shops/${shop.id}`);
    wsRef.current = ws;
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "status_update" || msg.type === "initial") {
        qc.setQueryData(["embed-shop", slug], (old: Shop | undefined) =>
          old ? { ...old, status: msg.status, wait_time: msg.wait_time } : old
        );
      }
    };
    return () => ws.close();
  }, [shop?.id]);

  const STATUS_COLORS: Record<string, string> = {
    open: "#16a34a",
    busy: "#d97706",
    closed: "#9ca3af",
  };

  const STATUS_BG: Record<string, string> = {
    open: "#f0fdf4",
    busy: "#fffbeb",
    closed: "#f9fafb",
  };

  if (isLoading || !shop) {
    return (
      <div style={{ fontFamily: "system-ui,sans-serif", padding: "16px", color: "#9ca3af", fontSize: "14px" }}>
        …
      </div>
    );
  }

  const color = STATUS_COLORS[shop.status] ?? STATUS_COLORS.closed;
  const bg = STATUS_BG[shop.status] ?? STATUS_BG.closed;
  const shopUrl = `${window.location.origin}/shops/${shop.slug}`;

  return (
    <div style={{
      fontFamily: "system-ui,-apple-system,sans-serif",
      background: bg,
      padding: "16px 20px",
      height: "100%",
      boxSizing: "border-box",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "12px",
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, display: "inline-block", flexShrink: 0 }} />
          <span style={{ fontWeight: 700, fontSize: "15px", color: "#111827", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {shop.name}
          </span>
        </div>
        {shop.location && (
          <div style={{ fontSize: "12px", color: "#6b7280", marginBottom: "6px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {shop.location}
          </div>
        )}
        {shop.status !== "closed" ? (
          <div style={{ display: "flex", alignItems: "baseline", gap: "4px" }}>
            <span style={{ fontSize: "28px", fontWeight: 800, color, lineHeight: 1 }}>{shop.wait_time}</span>
            <span style={{ fontSize: "13px", color: "#6b7280" }}>{t("embed.wait")}</span>
          </div>
        ) : (
          <div style={{ fontSize: "14px", color: "#9ca3af" }}>{t("embed.closed")}</div>
        )}
      </div>

      {shop.status !== "closed" && (
        <a href={shopUrl} target="_blank" rel="noopener noreferrer" style={{
          display: "inline-block",
          background: "#7e22ce",
          color: "#fff",
          padding: "8px 14px",
          borderRadius: "8px",
          fontSize: "13px",
          fontWeight: 600,
          textDecoration: "none",
          whiteSpace: "nowrap",
          flexShrink: 0,
        }}>
          {t("embed.book")}
        </a>
      )}
    </div>
  );
}
