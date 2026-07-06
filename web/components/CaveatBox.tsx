export default function CaveatBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="caveat-box">
      <span aria-hidden>⏳</span>
      <span>{children}</span>
    </div>
  );
}
