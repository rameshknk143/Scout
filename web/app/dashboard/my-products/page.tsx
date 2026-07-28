import MyProductsClient from "./my-products-client";

export default function MyProductsPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-900 font-sans">My Products</h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">
        Track your active product listings, log sourcing unit costs, and audit target gross margins.
      </p>
      <MyProductsClient />
    </div>
  );
}
