import InventoryClient from "./inventory-client";

export default function InventoryPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-white font-sans">Inventory Operations</h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">
        Monitor stock levels, track product re-order lead times, and estimate stock velocities to predict stock-out dates.
      </p>
      <InventoryClient />
    </div>
  );
}
