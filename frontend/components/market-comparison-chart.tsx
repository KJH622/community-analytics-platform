"use client";

import ReactECharts from "echarts-for-react";

import { MarketComparisonPoint } from "@/lib/api";

type MarketComparisonChartProps = {
  data: MarketComparisonPoint[];
};

function formatMarketValue(value: number | null | undefined) {
  if (value == null) {
    return "-";
  }
  return value.toLocaleString("ko-KR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
}

function formatHateValue(value: number | null | undefined) {
  if (value == null) {
    return "-";
  }
  return value.toLocaleString("ko-KR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function MarketComparisonChart({ data }: MarketComparisonChartProps) {
  return (
    <ReactECharts
      style={{ height: 360 }}
      option={{
        backgroundColor: "transparent",
        animationDuration: 500,
        tooltip: {
          trigger: "axis",
          formatter: (params: Array<{ seriesName: string; dataIndex: number; value: number | null }>) => {
            if (!params.length) {
              return "";
            }

            const point = data[params[0].dataIndex];
            const lines = [`${point.date}`];

            params.forEach((item) => {
              if (item.seriesName === "경제 혐오지수") {
                lines.push(`${item.seriesName}: ${formatHateValue(item.value)}`);
                return;
              }

              const isCarried =
                item.seriesName === "코스피" ? point.kospi_is_carried : point.kosdaq_is_carried;
              const suffix = isCarried ? " (휴장일, 직전 종가)" : "";
              lines.push(`${item.seriesName}: ${formatMarketValue(item.value)}${suffix}`);
            });

            return lines.join("<br/>");
          },
        },
        legend: {
          top: 0,
          textStyle: { color: "#403d39" },
        },
        grid: { left: 56, right: 132, top: 56, bottom: 36 },
        xAxis: {
          type: "category",
          data: data.map((item) => item.date.slice(5)),
          axisLabel: { color: "#63615d" },
          axisLine: { lineStyle: { color: "#b9ae9f" } },
        },
        yAxis: [
          {
            type: "value",
            name: "코스피",
            position: "left",
            scale: true,
            axisLabel: {
              color: "#2e8b57",
              formatter: (value: number) => formatMarketValue(value),
            },
            axisLine: { show: true, lineStyle: { color: "#2e8b57" } },
            splitLine: { lineStyle: { color: "#d8cec1" } },
          },
          {
            type: "value",
            name: "코스닥",
            position: "right",
            scale: true,
            axisLabel: {
              color: "#1f5f8b",
              formatter: (value: number) => formatMarketValue(value),
            },
            axisLine: { show: true, lineStyle: { color: "#1f5f8b" } },
            splitLine: { show: false },
          },
          {
            type: "value",
            name: "혐오지수",
            position: "right",
            offset: 72,
            scale: true,
            axisLabel: {
              color: "#c84f3d",
              formatter: (value: number) => formatHateValue(value),
            },
            axisLine: { show: true, lineStyle: { color: "#c84f3d" } },
            splitLine: { show: false },
          },
        ],
        series: [
          {
            name: "코스피",
            type: "line",
            yAxisIndex: 0,
            smooth: true,
            showSymbol: false,
            data: data.map((item) => item.kospi_close),
            lineStyle: { color: "#2e8b57", width: 3 },
            itemStyle: { color: "#2e8b57" },
          },
          {
            name: "코스닥",
            type: "line",
            yAxisIndex: 1,
            smooth: true,
            showSymbol: false,
            data: data.map((item) => item.kosdaq_close),
            lineStyle: { color: "#1f5f8b", width: 3 },
            itemStyle: { color: "#1f5f8b" },
          },
          {
            name: "경제 혐오지수",
            type: "line",
            yAxisIndex: 2,
            smooth: true,
            showSymbol: false,
            data: data.map((item) => item.hate_index),
            lineStyle: { color: "#c84f3d", width: 3 },
            itemStyle: { color: "#c84f3d" },
            areaStyle: { color: "#c84f3d16" },
          },
        ],
      }}
    />
  );
}
