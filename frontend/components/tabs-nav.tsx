type TabsNavProps = {
  activeTab: "market" | "politics";
};

export function TabsNav({ activeTab }: TabsNavProps) {
  return (
    <div className="tabs" aria-label="대시보드 탭">
      <a href="/?tab=market" className={`tab ${activeTab === "market" ? "active-market" : ""}`}>
        경제
      </a>
      <a
        href="/?tab=politics"
        className={`tab ${activeTab === "politics" ? "active-politics" : ""}`}
      >
        정치
      </a>
    </div>
  );
}
