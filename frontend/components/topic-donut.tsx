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
          tooltip: { trigger: "item" },
          legend: { bottom: 0 },
          series: [
            {
              type: "pie",
              radius: ["42%", "72%"],
              data: data.map((item) => ({ name: item.topic, value: item.documents })),
              itemStyle: {
                borderColor: "#f4efe7",
                borderWidth: 4
              }
            }
          ]
        }}
      />
    </div>
  );
}
