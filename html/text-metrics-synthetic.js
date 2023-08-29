let Plot;
import("https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm").then(module => {
  Plot = module;


  let clean = prepareDataSummary(dataSummary)

  const div = document.querySelector("#container");
  
  // TEXT LENGTHS PLOT
  // 1. Extract unique licenseUseClass values
  let uniqueSyntheticClasses = Array.from(new Set(clean.map(d => d.syntheticClass)));
  
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
      ...uniqueSyntheticClasses.map(synthetic => {
          return Plot.density(
              clean.filter(d => d.syntheticClass === synthetic),
              { x: "inputTextLen", y: "targetTextLen", stroke: "syntheticClass", strokeOpacity: 0.35, }
          )
      }),
      ...uniqueSyntheticClasses.map(synthetic => {
          return Plot.dot(
              clean.filter(d => d.syntheticClass === synthetic),
              // Plot.bin({ r: "count" }, { x: "inputTextLen", y: "targetTextLen", symbol: getShapeForLicense(licenseClass), stroke: getLicenseColor(licenseClass), thresholds: 100 })
              {
                  x: "inputTextLen",
                  y: "targetTextLen",
                  r: 3,
                  // stroke: getLicenseColor(licenseClass),
                  stroke: "syntheticClass",
                  // strokeOpacity: 0.55, 
                  // strokeWidth: 0.55,
                  // shape: shapeMapping[licenseClass]
                  // custom: (selection) => {
                  //     selection.append(getShapeForLicense(licenseClass));
                  // }
                  symbol: "syntheticClass"
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
          color: {
              type: "categorical",
              scheme: "category10"
          },
          symbol: { legend: true },
          marks: marks
      })
  );
  
  document.querySelector(`#${plotId}`).append(xdiv)
  document.querySelector(`#x${plotCount}div`).append(xaxis)
  
});