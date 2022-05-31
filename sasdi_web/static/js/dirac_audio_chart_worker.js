importScripts("https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js");
onmessage = function (event) {
  const { canvas, chart_config, width } = event.data;
  const audioChart = new Chart(canvas.getContext("2d"), chart_config);
  canvas.width = width * 1.8;
  audioChart.resize();
};
