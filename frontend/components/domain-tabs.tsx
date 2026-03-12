import Link from "next/link";

type DomainTabsProps = {
  active: "market" | "politics";
};

export function DomainTabs({ active }: DomainTabsProps) {
  return (
    <div className="domain-tabs-shell">
      <div className="domain-tabs-track">
        <Link className="domain-pill" data-active={active === "market"} href="/">
          Market
        </Link>
        <Link className="domain-pill" data-active={active === "politics"} href="/politics">
          Politics
        </Link>
      </div>
    </div>
  );
}
