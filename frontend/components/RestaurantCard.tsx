"use client";
import { ExternalLink, Star, MapPin, IndianRupee } from "lucide-react";

export interface Recommendation {
  rank: number;
  name: string;
  cuisine: string;
  rating: number;
  cost_for_two: number;
  rest_type: string;
  url: string;
  ai_explanation: string;
}

interface RestaurantCardProps {
  rec: Recommendation;
}

const RANK_COLORS = [
  "from-yellow-400 to-amber-500 text-white shadow-yellow-200",
  "from-slate-300 to-slate-400 text-white shadow-slate-100",
  "from-orange-300 to-orange-500 text-white shadow-orange-100",
  "from-blue-400 to-blue-500 text-white shadow-blue-100",
  "from-emerald-400 to-emerald-500 text-white shadow-emerald-100",
];

export function RestaurantCard({ rec }: RestaurantCardProps) {
  const cuisines = rec.cuisine
    ? rec.cuisine.split(",").map((c) => c.trim()).filter(Boolean)
    : [];

  const rankGradient = RANK_COLORS[(rec.rank ?? 1) - 1] ?? RANK_COLORS[4];

  return (
    <div className="group restaurant-card bg-white/80 backdrop-blur-sm rounded-3xl border border-gray-100 p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] transition-all duration-500 hover:-translate-y-1 flex flex-col gap-4 relative overflow-hidden">
      {/* Subtle background glow on hover */}
      <div className="absolute -right-16 -top-16 w-32 h-32 bg-red-50 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
      
      {/* Header: rank + name + rest_type */}
      <div className="flex items-start gap-4">
        <div
          className={`shrink-0 w-10 h-10 rounded-2xl bg-gradient-to-br flex items-center justify-center text-sm font-black shadow-lg ${rankGradient}`}
        >
          {rec.rank}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-900 text-lg leading-tight truncate group-hover:text-[#E23744] transition-colors duration-300">
            {rec.name}
          </h3>
          {rec.rest_type && (
            <div className="flex items-center gap-1.5 mt-1 text-gray-400">
              <MapPin size={12} />
              <span className="text-xs font-semibold tracking-wide uppercase">
                {rec.rest_type}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Cuisine tags */}
      {cuisines.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {cuisines.map((c) => (
            <span
              key={c}
              className="px-3 py-1 bg-gray-50 text-gray-600 text-[10px] sm:text-xs rounded-lg font-bold border border-gray-100/50 uppercase tracking-wider"
            >
              {c}
            </span>
          ))}
        </div>
      )}

      {/* Rating + Cost */}
      <div className="flex items-center justify-between py-2 border-y border-gray-50">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 rounded-lg">
            <Star size={14} fill="currentColor" stroke="none" />
            <span className="font-bold text-sm">{Number(rec.rating).toFixed(1)}</span>
          </div>
        </div>
        <div className="flex items-center gap-1 text-gray-700 font-bold text-sm">
          <IndianRupee size={14} className="text-[#E23744]" />
          <span>{rec.cost_for_two?.toLocaleString("en-IN")}</span>
          <span className="text-gray-400 font-normal text-xs ml-1">for two</span>
        </div>
      </div>

      {/* AI Explanation */}
      {rec.ai_explanation && (
        <div className="relative">
          <p className="text-gray-500 text-sm leading-relaxed pl-4 border-l-2 border-[#E23744]/20 italic group-hover:border-[#E23744] transition-colors duration-500">
            "{rec.ai_explanation}"
          </p>
        </div>
      )}

      {/* CTA */}
      {rec.url && rec.url !== "nan" && (
        <a
          href={rec.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 flex items-center justify-center gap-2 w-full py-3.5 rounded-2xl text-white text-sm font-bold shadow-lg shadow-red-200 transition-all duration-300 hover:shadow-red-300 hover:scale-[1.02] active:scale-[0.98]"
          style={{ backgroundColor: "#E23744" }}
        >
          View on Zomato
          <ExternalLink size={16} />
        </a>
      )}
    </div>
  );
}
