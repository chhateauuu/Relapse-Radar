import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

/**
 * A real OpenStreetMap (Leaflet) map of the Portland area, with each flagged
 * place marked by a numbered pin and its geofence radius. Tiles load from OSM,
 * so this needs a network connection. Uses div-icon markers (no image assets),
 * which avoids the usual Leaflet bundler icon issue.
 */
const PORTLAND = [45.5231, -122.6765];

export default function MiniMap({ places = [], className = "" }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);

  // A stable signature so the markers only rebuild when the places change.
  const key = useMemo(
    () =>
      JSON.stringify(
        places.map((p) => [p.lat, p.lng, p.label ?? "", p.radius_m ?? 0])
      ),
    [places]
  );

  const pts = useMemo(
    () => places.filter((p) => Number.isFinite(p.lat) && Number.isFinite(p.lng)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [key]
  );

  // Create the map once.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return undefined;
    const map = L.map(containerRef.current, {
      zoomControl: false,
      scrollWheelZoom: false,
      attributionControl: true,
    }).setView(PORTLAND, 12);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap contributors",
    }).addTo(map);

    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    setTimeout(() => map.invalidateSize(), 0);

    return () => {
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
    };
  }, []);

  // (Re)draw the markers whenever the places change.
  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();

    if (pts.length === 0) {
      map.setView(PORTLAND, 12);
      return;
    }

    const latlngs = [];
    pts.forEach((p, i) => {
      const icon = L.divIcon({
        className: "rr-pin",
        html: `<div style="display:flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:9999px;background:#dc2626;color:#fff;font:700 12px/1 ui-sans-serif,system-ui;box-shadow:0 1px 4px rgba(0,0,0,.4);border:2px solid #fff">${i + 1}</div>`,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });
      const marker = L.marker([p.lat, p.lng], { icon }).addTo(layer);
      if (p.label) marker.bindTooltip(p.label, { direction: "top", offset: [0, -12] });

      if (Number.isFinite(p.radius_m) && p.radius_m > 0) {
        L.circle([p.lat, p.lng], {
          radius: p.radius_m,
          color: "#dc2626",
          weight: 1,
          fillColor: "#dc2626",
          fillOpacity: 0.12,
        }).addTo(layer);
      }
      latlngs.push([p.lat, p.lng]);
    });

    if (latlngs.length === 1) {
      map.setView(latlngs[0], 14);
    } else {
      map.fitBounds(L.latLngBounds(latlngs).pad(0.35));
    }
    setTimeout(() => map.invalidateSize(), 0);
  }, [pts]);

  return (
    <div
      ref={containerRef}
      className={`h-44 w-full overflow-hidden rounded-2xl ring-1 ring-slate-200 ${className}`}
    />
  );
}
