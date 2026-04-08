export function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm flex flex-col gap-3">
      <div className="flex items-start gap-3">
        <div className="skeleton w-8 h-8 rounded-full shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="skeleton h-4 w-3/4 rounded" />
          <div className="skeleton h-3 w-1/3 rounded" />
        </div>
      </div>
      <div className="flex gap-2">
        <div className="skeleton h-5 w-20 rounded-full" />
        <div className="skeleton h-5 w-16 rounded-full" />
      </div>
      <div className="flex gap-4">
        <div className="skeleton h-4 w-12 rounded" />
        <div className="skeleton h-4 w-24 rounded" />
      </div>
      <div className="skeleton h-14 w-full rounded" />
      <div className="skeleton h-10 w-full rounded-xl" />
    </div>
  );
}
