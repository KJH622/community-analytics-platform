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
          grid: { left: 28, right: 18, top: 20, bottom: 30 },
          xAxis: {
            type: "category",
            data: data.map((item) => item.label),
            axisLine: { lineStyle: { color: "rgba(19, 32, 51, 0.14)" } },
            axisTick: { show: false },
            axisLabel: { color: "#5c6b80" },
          },
          yAxis: {
            type: "value",
            axisLabel: { color: "#5c6b80" },
            splitLine: { lineStyle: { color: "rgba(19, 32, 51, 0.08)" } },
          },
          series: [
            {
              type: "line",
              smooth: true,
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
                    { offset: 0, color: `${color}55` },
                    { offset: 1, color: `${color}08` },
                  ],
                },
              },
              symbol: "circle",
              symbolSize: 7,
              itemStyle: {
                color,
                borderColor: "#ffffff",
                borderWidth: 2,
              },
            },
          ],
          tooltip: {
            trigger: "axis",
            backgroundColor: "rgba(15, 23, 42, 0.92)",
            borderWidth: 0,
            textStyle: { color: "#f8fafc" },
          },
        }}
      />
    </div>
  );
}
