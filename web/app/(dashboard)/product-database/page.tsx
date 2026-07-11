import ProductDatabaseClient from "./product-database-client";

export default function ProductDatabasePage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-950">Amazon Product Database</h1>
      <p className="text-zinc-500 text-xs font-medium mt-1 mb-6">
        Search and filter the complete database of bestseller category snapshots collected by your nightly crawler.
      </p>
      <ProductDatabaseClient />
    </div>
  );
}
