"use client";

import ReactECharts from "echarts-for-react";

type SeriesPoint = {
  label: string;
  value: number;
};

type ChartPanelProps = {
  title: string;
  data: SeriesPoint[];
  color?: string;
};

export function ChartPanel({ title, data, color = "#b5532f" }: ChartPanelProps) {
  return (
    <div className="panel">
      <h2 className="panel-title">{title}</h2>
      <ReactECharts
        style={{ height: 280 }}
        option={{
          backgroundColor: "transparent",
          grid: { left: 36, right: 16, top: 16, bottom: 34 },
          xAxis: {
            type: "category",
            data: data.map((item) => item.label),
            axisLabel: { color: "#63615d" }
          },
          yAxis: {
            type: "value",
            axisLabel: { color: "#63615d" },
            splitLine: { lineStyle: { color: "#d8cec1" } }
          },
          series: [
            {
              type: "line",
              smooth: true,
              data: data.map((item) => item.value),
              lineStyle: { color, width: 3 },
              areaStyle: { color: `${color}33` },
              symbol: "circle",
              symbolSize: 8
            }
          ],
          tooltip: { trigger: "axis" }
        }}
      />
    </div>
  );
}
