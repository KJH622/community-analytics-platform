"use client";

import ReactECharts from "echarts-for-react";

type TopicDonutProps = {
  title: string;
  data: { topic: string; documents: number }[];
};

export function TopicDonut({ title, data }: TopicDonutProps) {
  return (
    <div className="panel">
      <h2 className="panel-title">{title}</h2>
      <ReactECharts
        style={{ height: 280 }}
        option={{
          backgroundColor: "transparent",
          tooltip: {
            trigger: "item",
            backgroundColor: "rgba(15, 23, 42, 0.92)",
            borderWidth: 0,
            textStyle: { color: "#f8fafc" },
          },
          legend: {
            bottom: 0,
            textStyle: { color: "#5c6b80" },
          },
          series: [
            {
              type: "pie",
              radius: ["42%", "72%"],
              data: data.map((item) => ({ name: item.topic, value: item.documents })),
              itemStyle: {
                borderColor: "#f8fbff",
                borderWidth: 4,
              },
            },
          ],
        }}
      />
    </div>
  );
}
