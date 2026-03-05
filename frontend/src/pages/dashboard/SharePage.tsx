import { useState, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { QRCodeCanvas } from "qrcode.react";
import { shopApi } from "../../api";

export default function SharePage() {
  const { t } = useTranslation();
  const { data: shop } = useQuery({ queryKey: ["me"], queryFn: shopApi.me });
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedEmbed, setCopiedEmbed] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  if (!shop) return null;

  const origin = window.location.origin;
  const shopUrl = `${origin}/shops/${shop.slug}`;
  const embedUrl = `${origin}/embed/shops/${shop.slug}`;
  const embedSnippet = `<iframe\n  src="${embedUrl}"\n  width="320"\n  height="160"\n  frameborder="0"\n  style="border-radius:12px;border:1px solid #e5e7eb;"\n></iframe>`;

  function copyLink() {
    navigator.clipboard.writeText(shopUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  }

  function copyEmbed() {
    navigator.clipboard.writeText(embedSnippet);
    setCopiedEmbed(true);
    setTimeout(() => setCopiedEmbed(false), 2000);
  }

  function downloadQR() {
    const canvas = document.querySelector<HTMLCanvasElement>("#qr-canvas canvas");
    if (!canvas) return;
    const url = canvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = url;
    a.download = `${shop?.slug ?? "shop"}-qr.png`;
    a.click();
  }

  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-2xl font-bold">{t("share.title")}</h1>

      {/* QR Code */}
      <div className="card space-y-4">
        <div>
          <h2 className="font-semibold text-lg">{t("share.qr_title")}</h2>
          <p className="text-sm text-gray-500 mt-0.5">{t("share.qr_desc")}</p>
        </div>
        <div id="qr-canvas" className="flex justify-center py-2">
          <div className="p-4 bg-white rounded-xl border border-gray-100 shadow-sm inline-block">
            <QRCodeCanvas value={shopUrl} size={180} includeMargin />
          </div>
        </div>
        <button onClick={downloadQR} className="btn-secondary w-full">
          {t("share.download_qr")}
        </button>
      </div>

      {/* Direct link */}
      <div className="card space-y-3">
        <h2 className="font-semibold text-lg">{t("share.page_link")}</h2>
        <div className="flex gap-2">
          <input className="input flex-1 text-sm bg-gray-50" readOnly value={shopUrl} />
          <button onClick={copyLink} className="btn-secondary shrink-0">
            {copiedLink ? t("share.copied") : t("share.copy")}
          </button>
        </div>
      </div>

      {/* Embed */}
      <div className="card space-y-3">
        <div>
          <h2 className="font-semibold text-lg">{t("share.embed_title")}</h2>
          <p className="text-sm text-gray-500 mt-0.5">{t("share.embed_desc")}</p>
        </div>
        {/* Live preview */}
        <div className="rounded-xl overflow-hidden border border-gray-200">
          <iframe src={embedUrl} width="100%" height="160" frameBorder="0" title="embed preview" />
        </div>
        <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs overflow-x-auto text-gray-700 whitespace-pre">
          {embedSnippet}
        </pre>
        <button onClick={copyEmbed} className="btn-secondary w-full">
          {copiedEmbed ? t("share.copied") : t("share.copy_code")}
        </button>
      </div>
    </div>
  );
}
