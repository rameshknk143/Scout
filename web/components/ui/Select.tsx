"use client";

// Shared styled <select> — dedupes the two slightly-different hand-written
// versions in trend-radar-client.tsx (category picker) and
// watchlist-client.tsx (verdict/category filters), which used the same
// colors but different class strings. Both now render identically.
export type SelectOption = { value: string; label: string };

export default function Select({
  value,
  onChange,
  options,
  placeholder,
  className = "",
}: {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  className?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`input w-auto ${className}`}
    >
      {placeholder !== undefined && (
        <option value="" className="bg-bg-elevated">
          {placeholder}
        </option>
      )}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value} className="bg-bg-elevated">
          {opt.label}
        </option>
      ))}
    </select>
  );
}
