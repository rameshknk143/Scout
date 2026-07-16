import ProductDatabaseClient from "./product-database-client";

export default function ProductDatabasePage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-white font-sans">Amazon Product Database</h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">
        Search and filter the complete database of bestseller category snapshots collected by your nightly crawler.
      </p>
      <ProductDatabaseClient />
    </div>
  );
}
