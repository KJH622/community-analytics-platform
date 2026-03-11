type FilterBarProps = {
  title?: string;
};

export function FilterBar({ title }: FilterBarProps) {
  return (
    <div className="panel">
      {title ? <h2 className="panel-title">{title}</h2> : null}
      <div className="filter-bar">
        <label className="field">
          <span>날짜</span>
          <input type="date" disabled defaultValue={new Date().toISOString().slice(0, 10)} />
        </label>
        <label className="field">
          <span>소스</span>
          <select disabled defaultValue="all">
            <option value="all">전체</option>
          </select>
        </label>
        <label className="field">
          <span>구간</span>
          <select disabled defaultValue="all">
            <option value="all">전체</option>
          </select>
        </label>
        <label className="field">
          <span>주제</span>
          <select disabled defaultValue="all">
            <option value="all">전체</option>
          </select>
        </label>
        <label className="field">
          <span>감정</span>
          <select disabled defaultValue="all">
            <option value="all">전체</option>
          </select>
        </label>
      </div>
    </div>
  );
}
