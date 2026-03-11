type FilterBarProps = {
  title?: string;
  description?: string;
};

export function FilterBar({ title, description }: FilterBarProps) {
  return (
    <div className="panel">
      {title ? <h2 className="panel-title">{title}</h2> : null}
      {description ? <p className="list-meta">{description}</p> : null}
      <div className="filter-bar">
        <label className="field">
          <span>Date</span>
          <input type="date" disabled defaultValue={new Date().toISOString().slice(0, 10)} />
        </label>
        <label className="field">
          <span>Source</span>
          <select disabled defaultValue="all">
            <option value="all">All</option>
          </select>
        </label>
        <label className="field">
          <span>Board</span>
          <select disabled defaultValue="all">
            <option value="all">All</option>
          </select>
        </label>
        <label className="field">
          <span>Topic</span>
          <select disabled defaultValue="all">
            <option value="all">All</option>
          </select>
        </label>
        <label className="field">
          <span>Sentiment</span>
          <select disabled defaultValue="all">
            <option value="all">All</option>
          </select>
        </label>
      </div>
    </div>
  );
}
