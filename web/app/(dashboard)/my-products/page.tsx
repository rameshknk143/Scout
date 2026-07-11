import MyProductsClient from "./my-products-client";

export default function MyProductsPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-950">My Products</h1>
      <p className="text-zinc-500 text-xs font-medium mt-1 mb-6">
        Track your active product listings, log sourcing unit costs, and audit target gross margins.
      </p>
      <MyProductsClient />
    </div>
  );
}
