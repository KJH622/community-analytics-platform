import Link from "next/link";

type DomainTabsProps = {
  active: "market" | "politics";
};

export function DomainTabs({ active }: DomainTabsProps) {
  return (
    <div className="panel" style={{ marginTop: 22, padding: 10 }}>
      <div className="tag-row">
        <Link className="tag" data-active={active === "market"} href="/">
          경제
        </Link>
        <Link className="tag" data-active={active === "politics"} href="/politics">
          정치
        </Link>
      </div>
    </div>
  );
}
