let Plot;
import("https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm").then(module => {
  Plot = module;

  let clean = prepareDataSummary(dataSummary)

  // 1. Extract unique licenseUseClass values
  let uniqueLicenseClasses = Array.from(new Set(clean.map(d => d.licenseUseCategory)));

  // 2. Create a mapping of licenseUseClass to distinct shapes
  const shapeMapping = {
    "commercial": "circle",
    "non-commercial": "cross",
    "academic": "diamond",
    "academic-or-unclear": "triangle",
    // ... add more as needed
  };

  function getShapeForLicense(licenseClass) {
    switch (licenseClass) {
      case 'all':
        return 'triangle'; // or custom SVG path
      case 'non-commercial':
        return 'cross'; // provide the path for a triangle
      case 'academic':
        return 'diamond'; // for a square/rectangle
      default:
        return 'circle';
    }
  }

  function getLicenseColor(licenseClass) {
    switch (licenseClass) {
      case 'Commercial':
        return 'green'; // or custom SVG path
      case 'Unspecified':
        return 'orange';
      case 'Non-Commercial':
        return 'yellow'; // provide the path for a triangle
      case 'Academic-Only':
        return 'red'; // for a square/rectangle
      default:
        return 'teal';
    }
  }

  const marks = [
    // Plot.density(clean, { x: "inputTextLen", y: "targetTextLen", stroke: "density" }),
    ...uniqueLicenseClasses.map(licenseClass => {
      return Plot.density(
        clean.filter(d => d.licenseUseCategory === licenseClass),
        { x: "inputTextLen", y: "targetTextLen", stroke: "licenseUseCategory", strokeOpacity: 0.35, }
      )
    }),
    ...uniqueLicenseClasses.map(licenseClass => {
      return Plot.dot(
        clean.filter(d => d.licenseUseCategory === licenseClass),
        // Plot.bin({ r: "count" }, { x: "inputTextLen", y: "targetTextLen", symbol: getShapeForLicense(licenseClass), stroke: getLicenseColor(licenseClass), thresholds: 100 })
        {
          x: "inputTextLen",
          y: "targetTextLen",
          r: 3,
          // stroke: getLicenseColor(licenseClass),
          stroke: "licenseUseCategory",
          // strokeOpacity: 0.55, 
          // strokeWidth: 0.55,
          // shape: shapeMapping[licenseClass]
          // custom: (selection) => {
          //     selection.append(getShapeForLicense(licenseClass));
          // }
          symbol: "licenseUseCategory"
          //bins
        }
      )
    }),
    Plot.tip(clean, Plot.pointer({ x: "inputTextLen", y: "targetTextLen", title: (d) => ["Collection Name: " + d.collection, "Dataset Name: " + d.datasetName, "Input Length: " + d.inputTextLen, "Target Length: " + d.targetTextLen].join("\n") })),
    Plot.axisY({ label: null, labelArrow: "none" }),
    Plot.axisX({ label: null, labelArrow: "none" })
  ];

  const plotDiv = document.createElement("div")
  plotDiv.setAttribute("class", "plotDiv")
  let plotCount = document.getElementsByClassName("plotDiv").length + 1 //count the existing plotDivs
  let plotId = `plotDiv${plotCount}` //assign a new id by incrementing count
  plotDiv.setAttribute("id", plotId)
  document.querySelector('#container').append(plotDiv) //append plotDiv to the parent container in index.html

  //LAYERED DENSITY IN ONE PLOT
  let title = document.createElement("h1")
  // title.append("plot title")

  let ydiv = document.createElement("div")
  ydiv.setAttribute("class", "ydiv")
  ydiv.setAttribute("id", `y${plotCount}div`)

  let yaxis = document.createElement("h2")
  yaxis.append("Target Text Length")
  yaxis.setAttribute("class", "yaxis")
  yaxis.setAttribute("id", `y${plotCount}axis`)

  // let horizontalElem = document.createElement("div")
  // horizontalElem.setAttribute("class", "horiz")

  let xdiv = document.createElement("div")
  xdiv.setAttribute("class", "xdiv")
  xdiv.setAttribute("id", `x${plotCount}div`)

  let xaxis = document.createElement("h2")
  xaxis.append("Input Text Length")
  xaxis.setAttribute("class", "xaxis")
  xaxis.setAttribute("id", `x${plotCount}axis`)


  // const category10Original = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',]; // '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'];

  document.querySelector(`#${plotId}`).append(title)
  document.querySelector(`#${plotId}`).append(ydiv)
  document.querySelector(`#y${plotCount}div`).append(yaxis)
  document.querySelector(`#${plotId}`).append(
    Plot.plot({
      inset: 10,
      grid: true,
      x: { type: "log" },
      y: { type: "log" },
      color: { //*NEW* COLOR MAPPING
        type: "categorical",
        domain: uniqueLicenseClasses,
        range: ["#1f77b4", "#d62728", '#2ca02c'] //category10 red, blue, green
      },
      symbol: {
        legend: true,
        range: ["circle", "times", "triangle"]
      }, //restrict category symbols
      marks: marks
    })
  );

  document.querySelector(`#${plotId}`).append(xdiv)
  document.querySelector(`#x${plotCount}div`).append(xaxis)
  
});