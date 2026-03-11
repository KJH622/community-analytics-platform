"use client";

import ReactECharts from "echarts-for-react";

import { MarketComparisonPoint } from "@/lib/api";

type MarketComparisonChartProps = {
  data: MarketComparisonPoint[];
};

export function MarketComparisonChart({ data }: MarketComparisonChartProps) {
  return (
    <ReactECharts
      style={{ height: 320 }}
      option={{
        backgroundColor: "transparent",
        tooltip: { trigger: "axis" },
        legend: { top: 0 },
        grid: { left: 36, right: 24, top: 48, bottom: 34 },
        xAxis: {
          type: "category",
          data: data.map((item) => item.date.slice(5)),
          axisLabel: { color: "#63615d" },
        },
        yAxis: {
          type: "value",
          min: 0,
          max: 100,
          axisLabel: { color: "#63615d" },
          splitLine: { lineStyle: { color: "#d8cec1" } },
        },
        series: [
          {
            name: "코스피",
            type: "line",
            smooth: true,
            data: data.map((item) => item.kospi_scaled),
            lineStyle: { color: "#2e8b57", width: 3 },
            itemStyle: { color: "#2e8b57" },
          },
          {
            name: "코스닥",
            type: "line",
            smooth: true,
            data: data.map((item) => item.kosdaq_scaled),
            lineStyle: { color: "#1f5f8b", width: 3 },
            itemStyle: { color: "#1f5f8b" },
          },
          {
            name: "혐오지수",
            type: "line",
            smooth: true,
            data: data.map((item) => item.hate_scaled),
            lineStyle: { color: "#c84f3d", width: 3 },
            itemStyle: { color: "#c84f3d" },
            areaStyle: { color: "#c84f3d16" },
          },
        ],
      }}
    />
  );
}
