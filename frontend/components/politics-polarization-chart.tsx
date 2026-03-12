"use client";

import ReactECharts from "echarts-for-react";

import { PoliticsPolarizationPoint } from "@/lib/api";

type PoliticsPolarizationChartProps = {
  data: PoliticsPolarizationPoint[];
};

export function PoliticsPolarizationChart({ data }: PoliticsPolarizationChartProps) {
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
          max: 100,
          axisLabel: { color: "#63615d", formatter: "{value}%" },
          splitLine: { lineStyle: { color: "#d8cec1" } },
        },
        series: [
          {
            name: "찬성",
            type: "line",
            smooth: true,
            data: data.map((item) => item.support_rate),
            lineStyle: { color: "#2e8b57", width: 3 },
            itemStyle: { color: "#2e8b57" },
            areaStyle: { color: "#2e8b5718" },
          },
          {
            name: "반대",
            type: "line",
            smooth: true,
            data: data.map((item) => item.oppose_rate),
            lineStyle: { color: "#c84f3d", width: 3 },
            itemStyle: { color: "#c84f3d" },
            areaStyle: { color: "#c84f3d14" },
          },
          {
            name: "중립",
            type: "line",
            smooth: true,
            data: data.map((item) => item.neutral_rate),
            lineStyle: { color: "#9a8359", width: 2 },
            itemStyle: { color: "#9a8359" },
          },
        ],
      }}
    />
  );
}
