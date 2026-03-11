type FilterBarProps = {
  action: string;
  defaults?: {
    date_from?: string;
    source?: string;
    country?: string;
    topic?: string;
    sentiment?: string;
  };
};

export function FilterBar({ action, defaults }: FilterBarProps) {
  return (
    <form className="filters" action={action}>
      <label>
        날짜
        <input type="date" name="date_from" defaultValue={defaults?.date_from} />
      </label>
      <label>
        소스
        <input
          type="text"
          name="source"
          placeholder="dcinside_stockus"
          defaultValue={defaults?.source}
        />
      </label>
      <label>
        국가
        <input type="text" name="country" placeholder="KR / US" defaultValue={defaults?.country} />
      </label>
      <label>
        주제
        <input type="text" name="topic" placeholder="inflation" defaultValue={defaults?.topic} />
      </label>
      <label>
        감정
        <select name="sentiment" defaultValue={defaults?.sentiment}>
          <option value="">전체</option>
          <option value="positive">긍정</option>
          <option value="negative">부정</option>
        </select>
      </label>
      <button type="submit">필터 적용</button>
    </form>
  );
}
