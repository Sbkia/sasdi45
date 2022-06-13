$(function () {
  videos_input = $("#videos_input");
  videos_dir_input = $("#videos_dir_input");
  sel_dir_btn = $("#sel_dir_btn");
  sel_serie_btn = $("#sel_serie_btn");
  sel_vids_btn = $("#sel_vids_btn");
  refresh_btn = $("#refresh_btn");
  unsel_vids_btn = $("#unsel_vids_btn");
  type = $("#type");
  first_frame_src = $("#first_frame_url").val();
  frame_img = $("#first_frame_win_img");
  file_name = $("#file_name");
  select_roi_btn = $("#select_roi_btn");
  select_series_roi_btn = $("#select_series_roi_btn");
  dir_relativePath = $("#dir_relativePath");
  input_file_back = null;
  select_roi_img_winbox = null;
  frame_img.hide();
  rois_input = $("#rois_input");
  main_wrapper = $("#main_wrapper");
  serie_subdir_names = $("#serie_subdir_names");
  start_detect_btn = $("#start_detect_btn button");
  nb_vids = $("#nb_vids");
  file_names = $("#file_names");

  sel_dir_btn.on("click", function () {
  """open the selection window"""
    videos_dir_input.click();
    input_file_back = videos_dir_input.clone();
    type.val("dir");
  });
  sel_serie_btn.on("click", function () {
  """open the selection window"""
    input_file_back = videos_dir_input.clone();
    videos_dir_input.click();
    type.val("series");
  });
  sel_vids_btn.on("click", function () {
  """open the selection window"""
    input_file_back = videos_input.clone();
    videos_input.click();
    type.val("files");
  });



  function set_file_change_handler() {
  /* take the selected files and call the put_videos function */
    main_wrapper.on("change", "#videos_input", function () {
      if (!$(this).val().length) {
        $(this).get().files = input_file_back.get().files;
        return;
      }
      videos_dir_input.val("");
      put_videos();
    });
    main_wrapper.on("change", "#videos_dir_input", function (e) {
      type_data = type.val() == "series" ? "s" : "v";
      if (!$(this).val().length) {
        $(this).get().files = input_file_back.get().files;
        return;
      }
      if (type_data == "s") {
        let files = e.target.files;
        let relativePaths = [];
        for (let i = 0; i < files.length; i++) {
          relativePaths[i] = files[i].webkitRelativePath;
        }
        dir_relativePath.val(JSON.stringify(relativePaths));
      }
      videos_input.val("");
      put_videos(type_data);
    });
  }
  set_file_change_handler();


  function put_videos(type = "v") {
  /*makes the link with url.py which calls api.py */
    is_series = type == "s";
    btn = is_series ? select_series_roi_btn : select_roi_btn;
    select_series_roi_btn.prop("disabled", true);  //disable buttons
    select_roi_btn.prop("disabled", true);         //disable buttons
    output = $("#select_vidget .output");
    roi_output = $("#roi_vidget .output");
    output.html(
      "ANALYSING SELECTED VIDEO(S), PLEASE WAIT ... <br>See terminal for more infos."
    );
    send_video_request("/put-videos");
  }

function send_video_request(url) {
    d = new Date();
    $.post({
      url: url,
      data: new FormData($("#select_videos_form")[0]),
      processData: false,
      contentType: false,
    })
      .fail(function (data) {
        //console.log(data);
      })
      .done(function (data) {
        output.html(data.result);
        btn.prop("disabled", false);
        start_detect_btn.prop("disabled", false);
        file_name.val(data.file_name);
        roi_output.html(data.roi_text);
        rois_input.val(JSON.stringify(data.rois));
        nb_vids.val(data.nb_vids);
        file_names.val(JSON.stringify(data.file_names_list));
        if (type.val() == "series") {
          serie_subdir_names.val(JSON.stringify(data.serie_subdir_names));
          data.rois.forEach((elt, index) => {
            main_wrapper.append(
              "<img class='serie_frame' src = '/get-first-serie-frame?index=" +
                index +
                "&" +
                d.getTime() +
                "'/>"
            );
          });
        }
      });
  }


 unsel_vids_btn.on("click", function () {
    send_video_request("/unselect");
    $(".files_selector").val("");
    rois_input.val("[]");
    rois_input.change();
  });

  refresh_btn.on("click", function (data) {
    refresh_btn.prop("disabled", true);
    output = $("#select_vidget .output");
    roi_output = $("#roi_vidget .output");
    $.get("/refresh", function (data) {
      output.html(data.output_test);
      refresh_btn.prop("disabled", false);
      roi_output.html(data.roi_text);
    });
  });
});


 select_roi_btn.on("click", function () {
    show_rois_windows();
  });



var show_img_height;
  function show_rois_windows(isSerie = false, series_index = 0) {
    d = new Date();
    var img_scr;
    var nbseries = 1;
    if (isSerie) {
      try {
        series = JSON.parse(rois_input.val());
        rois = series[series_index];
        subdir_name = JSON.parse(serie_subdir_names.val())[series_index];
        img_scr = $(".serie_frame").eq(series_index).attr("src");
        nbseries = series.length;
        title = "ROI selection for " + subdir_name;
      } catch (error) {}
    } else {
      filename = file_name.val();
      title = "ROI selection for " + filename;
      img_scr = first_frame_src;
      try {
        rois = JSON.parse(rois_input.val());
      } catch (error) {
        rois = [];
      }
    }
    $("<img src='" + img_scr + "?" + d.getTime() + "' />").on(
      "load",
      function (e) {
        image_height = e.target.naturalHeight;
        image_width = e.target.naturalWidth;
        screen_height = $(window).height();
        screen_width = $(window).width();
        // Check that image is smaller than screen or set a ratio to be around 70% of screen size
        ratio_width = 1;
        ratio_height = 1;
        if (image_width > screen_width * 0.8) {
          ratio_width =
            Math.round(10 * (screen_width / (image_width * 1.3))) / 10;
        }
        if (image_height > screen_height * 0.8) {
          ratio_height =
            Math.round(10 * (screen_height / (image_height * 1.3))) / 10;
        }
        // Keep the smallest ratio for BOTH DIMENSIONS
        ratio_image = Math.min(ratio_width, ratio_height);
        // Set ratioed dimension tuple (width, height)
        width = parseInt(ratio_image * image_width);
        height = parseInt(ratio_image * image_height);
        show_img_height = height;
        if (select_roi_img_winbox == null) {
          select_roi_img_winbox = new WinBox(title, {
            html:
              "<div class='rois_selector_label'><h2>" +
              title +
              "</h2><br>" +
              "R = Record current ROI <br>" +
              "D = Discard last ROI <br>" +
              "</div>",
            class: ["no-full", "no-max", "no-min", "rois-select-win"],
            background: "#5F9EA0",
            x: "center",
            y: "center",
            onclose: function () {
              select_roi_img_winbox = null;
              if (series_index != nbseries - 1) {
                show_rois_windows(isSerie, series_index + 1);
              }
            },
          });
        }
        wb_body = $(".rois-select-win .wb-body");
        wb_body.attr("tabindex", "0");
        try {
          rois.forEach((roi, i) => {
            wb_body.append(
              get_square(
                roi[0][0] * ratio_image,
                roi[0][1] * ratio_image,
                roi[1][0] * ratio_image,
                roi[1][1] * ratio_image,
                "",
                i + 1,
                isSerie,
                series_index
              )
            );
          });
        } catch (error) {
          rois = [];
        }
        select_roi_img_winbox.resize(width, height);
        wb_body.css("background", "url(" + img_scr + "?" + d.getTime() + ")");
        wb_body.css("background-size", "cover");
        wb_body.css("background-repeat", "no-repeat");
        wb_body.parent().css("padding-bottom", "35px");
        select_roi_img_winbox.show();
        var index;
        wb_body
          .on("mousedown", function (e) {
            $(this).unbind("keydown");
            if (e.which == 1) {
              if (isSerie) {
                index = series[series_index].length + 1;
              } else {
                index = rois.length + 1;
              }
              if (index > 8) {
                return;
              }
              randomColor = Math.floor(Math.random() * 16777215).toString(16);
              var x = e.pageX - $(this).offset().left;
              var y = e.pageY - $(this).offset().top;
              $(".roi.unselected").remove();
              $(this).append(get_square(x, y, x, y, "unselected", index));
              $(this).on("mousemove", function (_e) {
                var _x = _e.pageX - $(this).offset().left;
                var _y = _e.pageY - $(this).offset().top;
                var w = _e.pageX - e.pageX;
                var h = _e.pageY - e.pageY;
                scare = $("#" + randomColor);
                if (w < 0) {
                  console.log("width negate");
                  scare.css("left", _x).width(-w);
                } else {
                  scare.width(w);
                }
                if (h < 0) {
                  scare.css("top", _y).height(-h);
                } else {
                  scare.height(h);
                }
              });
            }
          })
          .on("mouseup", function () {
            $(this).unbind("mousemove");
            $(this).on("keydown", function (e) {
              var code = e.keyCode || e.which;
              if (code == 82) {
                save_roi(index, ratio_image, isSerie, series_index);
              } else if (code == 68) {
                discard_last_roi(isSerie, series_index);
              }
            });
          });
      }
    );
  }
  var select_roi_img_winbox2 = null;


 // Selectionner ROIs pour les series
  select_series_roi_btn.on("click", function () {
    show_rois_windows(true);
  });



  function get_square(
    x1,
    y1,
    x2,
    y2,
    addClass = "",
    index = 0,
    isSerie = false,
    serie_index = 0
  ) {
    randomColor = Math.floor(Math.random() * 16777215).toString(16);
    var top = y1;
    var left = x1;
    var width = x2 - x1;
    var height = y2 - y1;
    if (index == 0) {
      rois = [];
      try {
        if (isSerie) {
          series = JSON.parse(rois_input.val());
          rois = series[serie_index];
        } else {
          rois = JSON.parse(rois_input.val());
        }
        index = rois.length + 1;
      } catch (error) {
        console.log(error);
        index = 1;
      }
    }
    return (
      "<div class='roi " +
      addClass +
      "' style='color: #" +
      randomColor +
      "; border-color: #" +
      randomColor +
      ";left:" +
      left +
      "px; top:" +
      top +
      "px; width: " +
      width +
      "px; height: " +
      height +
      "px;'; id=" +
      randomColor +
      " data-index=" +
      index +
      ">" +
      index +
      "</div>"
    );
  }


 $("#select_vidget .output").on("click", "span.file_infos", function () {
    $("span.file_infos.active").removeClass("active");
    $(this).addClass("active");
    $("#selected_vid_index").val($(this).index());
  });

  rois_input.on("change", function () {
    process_rois();
  });



  function process_rois() {
    $.post({
      url: "/save-rois",
      data: new FormData($("#select_videos_form")[0]),
      processData: false,
      contentType: false,
    })
      .fail(function (data) {
        //console.log(data);
      })
      .done(function (data) {
        roi_output.html(data.roi_text);
        rois_input.val(JSON.stringify(data.rois));
      });
  }

  function save_roi(index, ratio_image, isSerie = false, serie_index = 0) {
    roi_div = $(".roi[data-index='" + index + "']");
    width = roi_div.width();
    height = roi_div.height();
    parent = roi_div.parent();
    x1 = parseFloat(roi_div.css("left").replace("px", ""));
    y1 = parseFloat(roi_div.css("top").replace("px", ""));
    x2 = x1 + width;
    y2 = y1 + height;
    if (x1 > x2) {
      temp = x1;
      x1 = x2;
      x2 = temp;
      temp = y1;
      y1 = y2;
      y2 = temp;
    }
    try {
      if (isSerie) {
        series = JSON.parse(rois_input.val());
        rois = series[serie_index];
      } else {
        rois = JSON.parse(rois_input.val());
      }
      if (rois.length >= index) {
        return;
      }
    } catch (error) {
      rois = [];
    }
    if (isSerie) {
      series[serie_index].push([
        [parseInt(x1 / ratio_image), parseInt(y1 / ratio_image)],
        [parseInt(x2 / ratio_image), parseInt(y2 / ratio_image)],
      ]);
      rois_input.val(JSON.stringify(series));
    } else {
      rois.push([
        [parseInt(x1 / ratio_image), parseInt(y1 / ratio_image)],
        [parseInt(x2 / ratio_image), parseInt(y2 / ratio_image)],
      ]);
      rois_input.val(JSON.stringify(rois));
    }
    rois_input.change();
    roi_div.removeClass("unselected");
  }

  function discard_last_roi(isSerie = false, serie_index = 0) {
    roi_div = $(".roi.unselected");
    if (roi_div.length) {
      roi_div.remove();
      return;
    } else {
      try {
        if (isSerie) {
          series = JSON.parse(rois_input.val());
          $(".roi")
            .eq(series[serie_index].length - 1)
            .remove();
          series[serie_index].pop();
          rois_input.val(JSON.stringify(series));
        } else {
          rois = JSON.parse(rois_input.val());
          $(".roi")
            .eq(rois.length - 1)
            .remove();
          rois.pop();
          rois_input.val(JSON.stringify(rois));
        }
        rois_input.change();
      } catch (error) {
        return;
      }
    }
  }


  start_detect_btn.on("click", function () {
    $(this).prop("disabled", true);
    output = $("#detect_output .output");
    data = {
      admit_reanalise: $("#admit_reanalise").is(":checked"),
      nb_threads: $("#nb_threads").val(),
      csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").eq(0).val(),
    };
    $.post({
      url: "/start-analysis",
      data: data,
    })
      .fail(function (data) {
        //console.log(data);
      })
      .done(function (_data) {
        output.html(_data.message);
        if (!data.stop) {
          $.post({
            url: "/process-analysis",
            data: data,
          })
            .fail(function (data) {
              //console.log(data);
            })
            .done(function (data) {
              output.html(data.message);
              names = JSON.parse(file_names.val());
              html = "<h1>Show results for </h1>";
              if (type.val() == "files" || type.val() == "dir") {
                names.forEach((name, index) => {
                  html +=
                    "<a href='#' class='result_link' data-index=" +
                    index +
                    " data-serie_index=-1 >" +
                    name +
                    "</a>";
                });
              } else {
                var i = 0;
                var j = 0;
                for (const [key, value] of Object.entries(names)) {
                  html += "<h3>" + key + "</h3>";
                  value.forEach((name, index) => {
                    html +=
                      "<a href='#' class='result_link' data-index=" +
                      i++ +
                      " data-serie_index=" +
                      j +
                      ">" +
                      name +
                      "</a>";
                  });
                  j++;
                }
              }
              $("#result_links").html(html);
              $("#result_links .result_link").on("click", function (e) {
                e.preventDefault();
                show_result_window(
                  $(this).data("index"),
                  $(this).data("serie_index")
                );
              });
            })
            .always(function () {
              start_detect_btn.prop("disabled", false);
            });
        } else {
          start_detect_btn.prop("disabled", false);
        }
      });
  });

var result_window = null;
  function show_result_window(index, serie_index) {
    if (result_window == null) {
      result_window = new WinBox("View Results", {
        url: "/results?index=" + index + "&serie_index=" + serie_index,
        background: "#5F9EA0",
        x: "center",
        y: "center",
        onclose: function () {
          result_window = null;
        },
      });
    }
}
