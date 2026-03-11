"use client";

import ReactECharts from "echarts-for-react";

import type { HourlyComparisonPoint } from "@/lib/api";

type HourlyComparisonPanelProps = {
  data: HourlyComparisonPoint[];
};

function formatSignedPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }

  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function getAverageHateIndex(data: HourlyComparisonPoint[]) {
  const values = data
    .map((point) => point.hate_index)
    .filter((value): value is number => value !== null && !Number.isNaN(value));

  if (values.length === 0) {
    return null;
  }

  return Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2));
}

function toHourLabel(label: string) {
  return label.slice(11, 16);
}

export function HourlyComparisonPanel({ data }: HourlyComparisonPanelProps) {
  const averageHateIndex = getAverageHateIndex(data);
  const labels = data.map((item) => toHourLabel(item.label));

  return (
    <section className="panel comparison-panel">
      <div className="comparison-header">
        <div>
          <span className="section-label">Hourly Compare</span>
          <h2 className="panel-title">시간대별 혐오지수 vs 나스닥·코스피</h2>
          <p className="comparison-copy">
            혐오지수는 원값, 시장은 최근 24시간 기준 변동률로 맞춰서 같은 시간축에서 비교합니다.
          </p>
        </div>

        <div className="comparison-legend">
          <span className="legend-dot legend-hate">혐오지수</span>
          <span className="legend-dot legend-kospi">코스피</span>
          <span className="legend-dot legend-nasdaq">나스닥</span>
        </div>
      </div>

      <div className="comparison-note">최근 구간 평균 혐오지수 {averageHateIndex?.toFixed(1) ?? "-"}</div>

      <ReactECharts
        notMerge
        lazyUpdate
        className="comparison-chart"
        style={{ height: 460 }}
        option={{
          backgroundColor: "transparent",
          color: ["#be5a2f", "#147d72", "#2f68e7"],
          animationDuration: 900,
          animationEasing: "cubicOut",
          grid: {
            left: 62,
            right: 68,
            top: 70,
            bottom: 42,
          },
          xAxis: {
            type: "category",
            boundaryGap: false,
            data: labels,
            axisLine: {
              lineStyle: { color: "rgba(19, 32, 51, 0.08)" },
            },
            axisTick: { show: false },
            axisLabel: {
              color: "#6b7a90",
              fontSize: 13,
              fontWeight: 600,
              margin: 14,
              interval: 2,
            },
          },
          yAxis: [
            {
              type: "value",
              min: 0,
              max: 100,
              axisLabel: {
                color: "#6b7a90",
                fontSize: 12,
                margin: 10,
              },
              axisLine: { show: false },
              axisTick: { show: false },
              splitLine: {
                lineStyle: {
                  color: "rgba(19, 32, 51, 0.07)",
                },
              },
            },
            {
              type: "value",
              min: 0,
              max: 5,
              position: "right",
              axisLabel: {
                color: "#6b7a90",
                fontSize: 12,
                formatter: "{value}%",
                margin: 10,
              },
              axisLine: { show: false },
              axisTick: { show: false },
              splitLine: { show: false },
            },
          ],
          tooltip: {
            trigger: "axis",
            axisPointer: {
              type: "line",
              lineStyle: {
                color: "rgba(19, 32, 51, 0.18)",
                width: 1,
              },
            },
            backgroundColor: "rgba(15, 23, 42, 0.92)",
            borderWidth: 0,
            padding: 14,
            textStyle: { color: "#f8fafc", fontSize: 12 },
            formatter: (params: Array<{ dataIndex: number }>) => {
              const point = data[params[0]?.dataIndex ?? 0];
              const lines = [
                `<strong>${point.label}</strong>`,
                `혐오지수 ${point.hate_index?.toFixed(1) ?? "-"}`,
                `평균 혐오지수 ${averageHateIndex?.toFixed(1) ?? "-"}`,
                `코스피 ${formatSignedPercent(point.kospi_change_pct)}`,
                `나스닥 ${formatSignedPercent(point.nasdaq_change_pct)}`,
                `게시글 수 ${point.post_count}`,
              ];

              if (point.post_count === 0) {
                lines.push("게시글이 없는 시간대라 혐오지수도 비어 있습니다.");
              }

              return lines.join("<br/>");
            },
          },
          graphic: [
            {
              type: "text",
              left: 0,
              top: 12,
              style: {
                text: "혐오지수",
                fill: "#7b8798",
                fontSize: 13,
                fontWeight: 700,
              },
            },
            {
              type: "text",
              right: 0,
              top: 12,
              style: {
                text: "지수 변동률",
                fill: "#7b8798",
                fontSize: 13,
                fontWeight: 700,
                align: "right",
              },
            },
          ],
          series: [
            {
              name: "혐오지수",
              type: "line",
              yAxisIndex: 0,
              smooth: 0.55,
              connectNulls: false,
              data: data.map((item) => item.hate_index),
              symbol: "circle",
              symbolSize: 10,
              showSymbol: true,
              itemStyle: {
                color: "#be5a2f",
                borderColor: "#f8fafc",
                borderWidth: 2.5,
              },
              lineStyle: {
                color: "#be5a2f",
                width: 4.5,
                cap: "round",
                join: "round",
              },
              areaStyle: {
                color: "rgba(190, 90, 47, 0.10)",
              },
              markLine:
                averageHateIndex === null
                  ? undefined
                  : {
                      symbol: "none",
                      label: {
                        show: true,
                        formatter: `평균 ${averageHateIndex.toFixed(1)}`,
                        color: "#8b5cf6",
                        fontWeight: 700,
                        backgroundColor: "rgba(255,255,255,0.92)",
                        padding: [4, 8],
                        borderRadius: 999,
                      },
                      lineStyle: {
                        color: "#8b5cf6",
                        width: 2,
                        type: "dashed",
                      },
                      data: [{ yAxis: averageHateIndex }],
                    },
              emphasis: {
                focus: "series",
              },
              z: 3,
            },
            {
              name: "코스피",
              type: "line",
              yAxisIndex: 1,
              smooth: 0.45,
              connectNulls: false,
              data: data.map((item) => item.kospi_change_pct),
              symbol: "none",
              lineStyle: {
                color: "#147d72",
                width: 3.5,
                cap: "round",
                join: "round",
              },
              emphasis: {
                focus: "series",
              },
              z: 2,
            },
            {
              name: "나스닥",
              type: "line",
              yAxisIndex: 1,
              smooth: 0.45,
              connectNulls: false,
              data: data.map((item) => item.nasdaq_change_pct),
              symbol: "none",
              lineStyle: {
                color: "#2f68e7",
                width: 3.5,
                type: "dashed",
                cap: "round",
                join: "round",
              },
              emphasis: {
                focus: "series",
              },
              z: 1,
            },
          ],
        }}
      />
    </section>
  );
}
