"use client";

import { useCallback, useEffect, useState } from "react";
import { MapPin, ChefHat, Sliders, Sparkles, UtensilsCrossed } from "lucide-react";
import { Combobox } from "@/components/Combobox";
import { RestaurantCard, type Recommendation } from "@/components/RestaurantCard";
import { SkeletonCard } from "@/components/SkeletonCard";
import { Toast } from "@/components/Toast";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

if (typeof window !== "undefined" && !USE_MOCK) {
  console.log("🚀 Zomato AI: Connecting to real backend at", API_BASE);
}

interface Filters {
  locations: string[];
  cuisines: string[];
  cost_range: { min: number; max: number };
}

export default function HomePage() {
  // ── Filter options state ─────────────────────────────────────────────────
  const [filters, setFilters] = useState<Filters | null>(null);
  const [filtersError, setFiltersError] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  // ── Form state ───────────────────────────────────────────────────────────
  const [location, setLocation] = useState("");
  const [costMin, setCostMin] = useState(0);
  const [costMax, setCostMax] = useState(0);
  const [cuisine, setCuisine] = useState("");
  const [minRating, setMinRating] = useState(3.0);
  const [extraPrefs, setExtraPrefs] = useState("");

  // ── Results state ────────────────────────────────────────────────────────
  const [results, setResults] = useState<Recommendation[] | null>(null);
  const [totalMatches, setTotalMatches] = useState(0);
  const [loading, setLoading] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // ── Load filters on mount ────────────────────────────────────────────────
  useEffect(() => {
    const loadFilters = async () => {
      if (USE_MOCK) {
        console.log("Using Mock Filters (Dynamic Import)...");
        try {
          // Dynamic import mock data to avoid static analysis crashes
          const { MOCK_FILTERS } = await import("./mocks");
          setTimeout(() => {
            setFilters(MOCK_FILTERS);
            setCostMin(MOCK_FILTERS.cost_range.min);
            setCostMax(MOCK_FILTERS.cost_range.max);
          }, 800);
        } catch (e) {
          console.error("Failed to load mock filters:", e);
          setFiltersError(true);
        }
        return;
      }

      try {
        const r = await fetch(`${API_BASE}/filters`);
        if (!r.ok) throw new Error(`Filters API returned ${r.status}`);
        const data: Filters = await r.json();
        setFilters(data);
        setCostMin(data.cost_range.min);
        setCostMax(data.cost_range.max);
        setConnectionError(null);
      } catch (err) {
        console.error("Failed to load filters:", err);
        setFiltersError(true);
        setConnectionError("The backend API service at " + API_BASE + " is currently unreachable.");
        setToastMsg("Could not connect to the real backend. Please check if it's running.");
      }
    };

    loadFilters();
  }, []);

  // ── Submit ───────────────────────────────────────────────────────────────
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setLoading(true);
      setResults(null);
      setHasSearched(true);
      setToastMsg(null);

      if (USE_MOCK) {
        console.log("Using Mock Recommendations (Dynamic Import)...");
        try {
          const { MOCK_RECOMMENDATIONS } = await import("./mocks");
          setTimeout(() => {
            setResults(MOCK_RECOMMENDATIONS);
            setTotalMatches(MOCK_RECOMMENDATIONS.length);
            setLoading(false);
          }, 1500);
        } catch (e) {
          console.error("Failed to load mock recs:", e);
          setToastMsg("Error loading mock data.");
          setLoading(false);
        }
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/recommend`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            location,
            min_cost: costMin,
            max_cost: costMax,
            cuisine,
            min_rating: minRating,
            extra_preferences: extraPrefs,
          }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }));
          throw new Error(err.detail ?? "Unknown error from server");
        }

        const data = await res.json();
        setResults(data.recommendations ?? []);
        setTotalMatches(data.total_matches_found ?? 0);
        setConnectionError(null);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "An unexpected error occurred.";
        if (msg.includes("Failed to fetch") || msg.includes("Network")) {
          setConnectionError("Backend unreachable. Please ensure the FastAPI server is running on port 8000.");
        }
        setToastMsg(`Error: ${msg}`);
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [location, costMin, costMax, cuisine, minRating, extraPrefs]
  );

  const rawBounds = filters?.cost_range ?? { min: 0, max: 5000 };
  const costBounds = {
    min: Math.floor(rawBounds.min / 50) * 50,
    max: Math.ceil(rawBounds.max / 50) * 50,
  };

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen" style={{ background: "var(--bg)" }}>
      {/* ── Header ── */}
      <header
        className="w-full py-4 px-6 flex items-center gap-3 shadow-sm"
        style={{ background: "#E23744" }}
      >
        <UtensilsCrossed size={26} className="text-white" />
        <div>
          <h1 className="text-white font-bold text-xl leading-tight tracking-tight">
            Zomato AI
          </h1>
          <p className="text-red-100 text-xs font-medium">
            Powered by Groq · llama3-70b
          </p>
        </div>
      </header>

      {/* ── Two-panel layout ── */}
      <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8 flex flex-col lg:flex-row gap-6">
        {/* ── LEFT: Preference Form ── */}
        <aside className="w-full lg:w-80 xl:w-96 shrink-0">
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-5">
              <Sliders size={18} style={{ color: "#E23744" }} />
              <h2 className="font-semibold text-gray-800 text-base">
                Your Preferences
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              {/* Location */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                  <MapPin size={13} style={{ color: "#E23744" }} />
                  Area in Bangalore
                </label>
                {filters ? (
                  <div id="location-select-wrapper">
                    <Combobox
                      options={filters.locations}
                      value={location}
                      onChange={setLocation}
                      placeholder="Select neighbourhood…"
                    />
                  </div>
                ) : (
                  <div className="skeleton h-10 w-full rounded-xl" />
                )}
              </div>

              {/* Budget Range */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-3">
                  <span style={{ color: "#E23744" }} className="font-bold text-xs">
                    ₹
                  </span>
                  Budget
                  <span className="ml-auto font-semibold text-gray-900 text-sm">
                    ₹{costMin.toLocaleString("en-IN")} –{" "}
                    ₹{costMax.toLocaleString("en-IN")}
                  </span>
                </label>
                <div className="flex flex-col gap-2.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 w-6">Min</span>
                    <input
                      id="budget-min-slider"
                      type="range"
                      min={costBounds.min}
                      max={costBounds.max}
                      step={50}
                      value={costMin}
                      disabled={!filters}
                      onChange={(e) => {
                        const v = Number(e.target.value);
                        setCostMin(Math.min(v, costMax - 50));
                      }}
                      className="flex-1"
                      style={
                        {
                          "--track-fill": `${
                            ((costMin - costBounds.min) /
                              (costBounds.max - costBounds.min)) *
                            100
                          }%`,
                        } as React.CSSProperties
                      }
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 w-6">Max</span>
                    <input
                      id="budget-max-slider"
                      type="range"
                      min={costBounds.min}
                      max={costBounds.max}
                      step={50}
                      value={costMax}
                      disabled={!filters}
                      onChange={(e) => {
                        const v = Number(e.target.value);
                        setCostMax(Math.max(v, costMin + 50));
                      }}
                      className="flex-1"
                    />
                  </div>
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>₹{costBounds.min.toLocaleString("en-IN")}</span>
                  <span>₹{costBounds.max.toLocaleString("en-IN")}</span>
                </div>
              </div>

              {/* Cuisine */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                  <ChefHat size={13} style={{ color: "#E23744" }} />
                  Cuisine
                </label>
                {filters ? (
                  <div id="cuisine-select-wrapper">
                    <Combobox
                      options={["All Cuisines", ...filters.cuisines]}
                      value={cuisine}
                      onChange={(v) =>
                        setCuisine(v === "All Cuisines" ? "" : v)
                      }
                      placeholder="All Cuisines"
                    />
                  </div>
                ) : (
                  <div className="skeleton h-10 w-full rounded-xl" />
                )}
              </div>

              {/* Minimum Rating */}
              <div>
                <label className="flex items-center justify-between text-sm font-medium text-gray-700 mb-2">
                  <span>Minimum Rating</span>
                  <span className="font-semibold text-gray-900">
                    ⭐ {minRating.toFixed(1)}+
                  </span>
                </label>
                <input
                  id="rating-slider"
                  type="range"
                  min={1.0}
                  max={5.0}
                  step={0.5}
                  value={minRating}
                  onChange={(e) => setMinRating(Number(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>1.0</span>
                  <span>5.0</span>
                </div>
              </div>

              {/* Additional Preferences */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                  <Sparkles size={13} style={{ color: "#E23744" }} />
                  Additional Preferences
                </label>
                <textarea
                  id="extra-prefs-textarea"
                  rows={3}
                  value={extraPrefs}
                  onChange={(e) => setExtraPrefs(e.target.value)}
                  placeholder="e.g. rooftop, family-friendly, quick service…"
                  className="w-full px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-300 resize-none transition-all"
                />
              </div>

              {/* Submit */}
              <button
                id="find-restaurants-btn"
                type="submit"
                disabled={loading || !filters || filtersError}
                className="w-full flex items-center justify-center gap-2.5 py-3 rounded-xl font-semibold text-white text-sm transition-all hover:opacity-90 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
                style={{ backgroundColor: "#E23744" }}
              >
                {loading ? (
                  <>
                    <span className="spinner" />
                    Finding restaurants…
                  </>
                ) : (
                  <>
                    <UtensilsCrossed size={16} />
                    Find Restaurants
                  </>
                )}
              </button>

              {/* Connection Error UI */}
              {connectionError && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl">
                  <p className="text-red-800 text-xs font-bold uppercase tracking-wider mb-1">
                    Connectivity Error
                  </p>
                  <p className="text-red-600 text-sm leading-relaxed">
                    {connectionError}
                  </p>
                  <button 
                    onClick={() => window.location.reload()}
                    className="mt-2 text-xs font-semibold text-red-700 underline hover:no-underline"
                  >
                    Retry Connection
                  </button>
                </div>
              )}
            </form>
          </div>
        </aside>

        {/* ── RIGHT: Results panel ── */}
        <main className="flex-1 min-w-0">
          {/* Initial idle state */}
          {!hasSearched && !loading && (
            <div className="flex flex-col items-center justify-center h-full min-h-72 text-center gap-4 py-16">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-inner"
                style={{ background: "#fde8ea" }}
              >
                <UtensilsCrossed size={32} style={{ color: "#E23744" }} />
              </div>
              <div>
                <p className="font-semibold text-gray-700 text-base">
                  Set your preferences and find your next favourite restaurant
                </p>
                <p className="text-gray-400 text-sm mt-1">
                  Our AI ranks the best matches just for you
                </p>
              </div>
            </div>
          )}

          {/* Loading skeletons */}
          {loading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          )}

          {/* Results */}
          {!loading && results !== null && (
            <>
              {results.length > 0 ? (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <p className="text-sm text-gray-500">
                      Showing top{" "}
                      <span className="font-semibold text-gray-800">
                        {results.length}
                      </span>{" "}
                      of{" "}
                      <span className="font-semibold text-gray-800">
                        {totalMatches}
                      </span>{" "}
                      matching restaurants
                    </p>
                    <span className="flex items-center gap-1 text-xs text-gray-400 font-medium">
                      <Sparkles size={12} style={{ color: "#E23744" }} />
                      Ranked by AI
                    </span>
                  </div>
                  <div id="results-container" className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                    {results.map((rec) => (
                      <RestaurantCard key={`${rec.rank}-${rec.name}`} rec={rec} />
                    ))}
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-full min-h-72 text-center gap-4 py-16">
                  <div
                    className="w-16 h-16 rounded-2xl flex items-center justify-center"
                    style={{ background: "#fde8ea" }}
                  >
                    <UtensilsCrossed size={32} style={{ color: "#E23744" }} />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-700 text-base">
                      No restaurants found
                    </p>
                    <p className="text-gray-400 text-sm mt-1">
                      Try relaxing your filters — wider budget, lower rating, or
                      different area.
                    </p>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* ── Toast ── */}
      {toastMsg && (
        <Toast message={toastMsg} onDismiss={() => setToastMsg(null)} />
      )}
    </div>
  );
}
