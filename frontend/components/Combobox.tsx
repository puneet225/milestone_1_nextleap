"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, Search } from "lucide-react";

interface ComboboxProps {
  options: string[];
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  label?: string;
}

export function Combobox({
  options,
  value,
  onChange,
  placeholder = "Search…",
  label,
}: ComboboxProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  const filtered = query
    ? options.filter((o) => o.toLowerCase().includes(query.toLowerCase()))
    : options;

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleSelect = (opt: string) => {
    onChange(opt);
    setOpen(false);
    setQuery("");
  };

  return (
    <div className="relative" ref={ref}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1.5">
          {label}
        </label>
      )}
      <button
        type="button"
        className="w-full flex items-center justify-between px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-700 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-red-200 transition-all"
        onClick={() => setOpen((o) => !o)}
      >
        <span className={value ? "text-gray-900 font-medium" : "text-gray-400"}>
          {value || placeholder}
        </span>
        <ChevronDown
          size={16}
          className={`text-gray-400 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="combo-dropdown">
          <div className="flex items-center gap-2 p-2 border-b border-gray-100">
            <Search size={14} className="text-gray-400 shrink-0" />
            <input
              autoFocus
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search…"
              className="flex-1 text-sm outline-none placeholder:text-gray-400"
            />
          </div>
          {filtered.length === 0 ? (
            <div className="p-3 text-sm text-gray-400 text-center">
              No results
            </div>
          ) : (
            filtered.map((opt) => (
              <div
                key={opt}
                className={`combo-option ${opt === value ? "active" : ""}`}
                onClick={() => handleSelect(opt)}
              >
                {opt}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
