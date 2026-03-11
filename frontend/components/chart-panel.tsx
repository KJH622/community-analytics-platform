"use client";

import ReactECharts from "echarts-for-react";

type SeriesPoint = {
  label: string;
  value: number;
};

type ChartPanelProps = {
  title: string;
  description?: string;
  data: SeriesPoint[];
  color?: string;
};

function formatValue(value: number) {
  return value.toLocaleString("ko-KR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  });
}

export function ChartPanel({ title, description, data, color = "#b5532f" }: ChartPanelProps) {
  const numericValues = data.map((item) => item.value);
  const minValue = numericValues.length ? Math.min(...numericValues) : 0;
  const maxValue = numericValues.length ? Math.max(...numericValues) : 0;
  const baseRange = maxValue - minValue;
  const padding = baseRange > 0 ? baseRange * 0.22 : Math.max(Math.abs(maxValue) * 0.08, 1);
  const axisMin = minValue >= 0 ? Math.max(0, minValue - padding) : minValue - padding;
  const axisMax = maxValue + padding;

  return (
    <div className="panel chart-panel">
      <div className="chart-panel-head">
        <h2 className="panel-title">{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>

      <ReactECharts
        style={{ height: 280 }}
        option={{
          backgroundColor: "transparent",
          animationDuration: 500,
          grid: { left: 44, right: 22, top: 16, bottom: 34 },
          xAxis: {
            type: "category",
            data: data.map((item) => item.label),
            boundaryGap: false,
            axisLabel: { color: "#66768b" },
            axisLine: { lineStyle: { color: "#d4dfec" } },
          },
          yAxis: {
            type: "value",
            scale: true,
            min: axisMin,
            max: axisMax,
            axisLabel: {
              color: "#66768b",
              formatter: (value: number) => formatValue(value),
            },
            splitLine: { lineStyle: { color: "#e3ebf5" } },
          },
          tooltip: {
            trigger: "axis",
            formatter: (params: Array<{ axisValue: string; value: number }>) => {
              if (!params.length) {
                return "";
              }
              return `${params[0].axisValue}<br/>${formatValue(params[0].value)}`;
            },
          },
          series: [
            {
              type: "line",
              smooth: true,
              showSymbol: false,
              data: data.map((item) => item.value),
              lineStyle: { color, width: 3 },
              areaStyle: {
                color: {
                  type: "linear",
                  x: 0,
                  y: 0,
                  x2: 0,
                  y2: 1,
                  colorStops: [
                    { offset: 0, color: `${color}44` },
                    { offset: 1, color: `${color}08` },
                  ],
                },
              },
            },
          ],
        }}
      />
    </div>
  );
}
