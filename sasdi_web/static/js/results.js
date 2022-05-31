$(function () {
  try {
    const ctx = document.getElementById("chart").getContext("2d");
    var NUMBER_CFG;
    //const labels = JSON.parse($("#labels").val());
    //const datasets = JSON.parse(JSON.parse('"' + $("#datasets").val() + '"'));
    const file_name = $("#filename").val();
    var colors = [];
    var timemin_right_limit;
    const index = $("#index").val();
    const serie_index = $("#serie_index").val();
    var labels = [];
    var datasets = [];

    fetch("/get-chart-data?index=" + index + "&serie_index=" + serie_index)
      .then((res) => {
        if (res.ok) return res.json();
        console.error(res.statusText);
      })
      .then((data) => {
        labels = JSON.parse(data.labels);
        console.log(labels);
        datasets = JSON.parse(data.datasets);
        timemin_right_limit = parseFloat(data.timemin_right_limit);
        NUMBER_CFG = JSON.parse(data.numbers_cfg);
        audio_labels = JSON.parse(data.audio_labels);
        audio_datasets = JSON.parse(data.audio_datasets);
        audio_index_left_limit = parseFloat(data.audio_index_left_limit);
        audio_index_right_limit = parseFloat(data.audio_index_right_limit);
        axe_audio_upper_limit = parseFloat(data.axe_audio_upper_limit);
        axe_audio_lower_limit = parseFloat(data.axe_audio_lower_limit);
        power_labels = JSON.parse(data.power_labels);
        power_datasets = JSON.parse(data.power_datasets);
        axe_power_upper_limit = parseFloat(data.axe_power_upper_limit);
        axe_power_lower_limit = parseFloat(data.axe_power_lower_limit);
        axe_power_left_limit = parseFloat(data.axe_power_left_limit);
        axe_power_right_limit = parseFloat(data.axe_power_right_limit);
        i = 0;
        datasets.forEach((set) => {
          randomColor = Math.floor(Math.random() * 16777215).toString(16);
          set["borderColor"] = "#" + randomColor;
          set["backgroundColor"] = "#" + randomColor;
          set["pointRadius"] = 0;
          power_datasets[i]["borderColor"] = "#" + randomColor;
          power_datasets[i]["backgroundColor"] = "#" + randomColor;
          power_datasets[i]["pointRadius"] = 0;
          colors[i++] = randomColor;
        });
      })
      .then(() => {
        create_motion_chart();
        contexts = [
          [
            "dirac_audio_chart",
            "dirac_audio_chart_worker.js",
            { labels: audio_labels, datasets: audio_datasets },
            "Total power",
            audio_index_right_limit,
            axe_audio_upper_limit,
            axe_audio_lower_limit,
            audio_index_left_limit,
          ],
          [
            "dirac_power_chart",
            "dirac_power_chart_worker.js",
            { labels: power_labels, datasets: power_datasets },
            "Total power",
            axe_power_right_limit,
            axe_power_upper_limit,
            axe_power_lower_limit,
            axe_power_left_limit,
          ],
        ];
        contexts.forEach((ctx) => {
          create_async_chart(
            document.getElementById(ctx[0]).transferControlToOffscreen(),
            ctx[1],
            ctx[2],
            ctx[3],
            ctx[4],
            ctx[5],
            ctx[6],
            ctx[7]
          );
        });
      });

    async function create_motion_chart() {
      const data = {
        labels: labels,
        datasets: datasets,
      };

      const chart = new Chart(
        ctx,
        get_chart_config(
          data,
          "Image motion (% of maximum)",
          timemin_right_limit,
          parseFloat(NUMBER_CFG["max"]),
          parseFloat(NUMBER_CFG["min"])
        )
      );
      build_squares();
    }

    function create_async_chart(
      canvas,
      worker_file_name,
      data,
      y_text,
      xmax,
      ymax,
      ymin = 0,
      xmin = 0
    ) {
      chart_config = get_chart_config(data, y_text, xmax, ymax, ymin, xmin);
      chart_worker = new Worker("/static/js/" + worker_file_name);
      width = $(window).width();
      chart_worker.postMessage({ canvas, chart_config, width }, [canvas]);
    }

    function get_chart_config(
      data,
      y_text,
      xmax,
      ymax,
      ymin = 0,
      xmin = 0
    ) {
      return {
        type: "line",
        data: data,
        options: {
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: "Chart for " + file_name,
            },
          },
          scales: {
            x: {
              title: {
                display: true,
                text: "Time (min)",
              },
              /*type: "linear",
              min: xmin,
              max: xmax,
              /*ticks: {
                // forces step size to be 50 units
                //stepSize: 0.1,
              },*/
            },
            y: {
              title: {
                display: true,
                text: y_text,
              },
              /*type: "linear",
              min: ymin,
              max: ymax,*/
            },
          },
        },
      };
    }
    function build_squares() {
      img_scr = $("#first_frame_src").val();
      first_frame_img = $("#first_frame_img");
      roi_coord = JSON.parse($("#roi_coord").val());
      $("<img src='" + img_scr + "' />").on("load", function (e) {
        image_height = e.target.naturalHeight;
        image_width = e.target.naturalWidth;
        ratio_width = 1;
        ratio_height = 1;
        if (image_width > 300 * 0.8) {
          ratio_width = Math.round(10 * (300 / (image_width * 1.3))) / 10;
        }
        if (image_height > 200 * 0.8) {
          ratio_height = Math.round(10 * (200 / (image_height * 1.3))) / 10;
        }
        // Keep the smallest ratio for BOTH DIMENSIONS
        ratio_image = Math.min(ratio_width, ratio_height);
        width = ratio_image * image_width;
        height = ratio_image * image_height;
        first_frame_img.height(height);
        first_frame_img.width(width);
        roi_coord.forEach((roi, i) => {
          console.log("[[X1, Y1], [X2, Y2]] == " + roi);
          x1 = roi[0][0] * ratio_image;
          y1 = roi[0][1] * ratio_image;
          x2 = roi[1][0] * ratio_image;
          y2 = roi[1][1] * ratio_image;
          first_frame_img.append(
            "<div class='preview_roi'  style='color: #" +
              colors[i] +
              "; border-color: #" +
              colors[i] +
              ";left:" +
              x1 +
              "px; top:" +
              y1 +
              "px; width: " +
              (x2 - x1) +
              "px; height: " +
              (y2 - y1) +
              "px;'></div>"
          );
        });
      });
    }
    //build_squares();

    /*const dirac_audio_chart_ctx = document
      .getElementById("dirac_audio_chart")
      .transferControlToOffscreen();
    const audio_labels = JSON.parse($("#audio_labels").val());
    const audio_datasets = JSON.parse(
      JSON.parse('"' + $("#audio_datasets").val() + '"')
    );
    const audio_data = {
      labels: audio_labels,
      datasets: audio_datasets,
    };

    const audio_max_value = parseFloat($("#audio_max_value").val());
    const audio_min_value = parseFloat($("#audio_min_value").val());

    const audio_config = {
      type: "line",
      data: audio_data,
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: "Chart for " + file_name,
          },
        },
        scales: {
          x: {
            title: {
              display: true,
              text: "Time (min)",
            },
            type: "linear",
            min: 0,
            max: timemin_right_limit,
          },
          y: {
            title: {
              display: true,
              text: "Audio Intensity (AU)",
            },
            type: "linear",
            min: audio_min_value,
            max: audio_max_value,
          },
        },
      },
    };
    /* const dirac_audio_chart_worker = new Worker(
      "/static/js/dirac_audio_chart_worker.js"
    );
    dirac_audio_chart_worker.postMessage(
      { dirac_audio_chart_ctx, audio_config },
      [dirac_audio_chart_ctx]
    );

    const dirac_power_chart_ctx = document
      .getElementById("dirac_power_chart")
      .transferControlToOffscreen();
    const power_labels = JSON.parse($("#power_labels").val());
    const power_datasets = JSON.parse(
      JSON.parse('"' + $("#power_datasets").val() + '"')
    );
    const power_data = {
      labels: power_labels,
      datasets: power_datasets,
    };

    const power_min_value = parseFloat($("#power_min_value").val());
    const power_max_value = parseFloat($("#power_max_value").val());

    const power_config = {
      type: "line",
      data: power_data,
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: "Chart for " + file_name,
          },
        },
        scales: {
          x: {
            title: {
              display: true,
              text: "Time (min)",
            },
            type: "linear",
            min: power_min_value,
            max: power_max_value,
          },
          y: {
            title: {
              display: true,
              text: "Total power",
            },
          },
        },
      },
    };
    /*const dirac_power_chart_worker = new Worker(
      "/static/js/dirac_power_chart_worker.js"
    );
    dirac_power_chart_worker.postMessage(
      { dirac_power_chart_ctx, power_config },
      [dirac_power_chart_ctx]
    );*/
  } catch (error) {
    console.log(error);
  }
});
