let collections = [];
let test;
let xstart;
let ystart;
let barWidth;
let barHeight;
let xspacing;
let yspacing;
let datasetBars;
let isStandardState;
let dataSummary;
let collectionTable;

function preload() {
  // load collections
  dataSummary = loadJSON(DATAFILE);
}

function setup() {
  // noLoop();
  createCanvas(windowWidth * 2, windowHeight * 1.2);

  isStandardState = true;

  xstart = 100;
  ystart = 100;
  barWidth = 100;
  barHeight = 3;
  xspacing = 30;
  yspacing = 10;

  datasetBars = [];

  dataClean();

  setupVis();
  displayInteraction();
}

function draw() {
  background("#151414");
  displayInteraction();
}

/** HELPER FUNCTIONS */

function dataClean() {
  //console.log(Object.values(dataSummary));

  collections = Object.values(dataSummary);

  //genearte unique colors for each collection
  collectionColors = [];
  let col2;
  let langCol;
  let licCol;

  collections.forEach((collection) => {
    
    /** ASSIGN COLLECTION COLOR
     * if collection colors includes the collection name (collection color has already been generated), find the first row that contains that collection and pull its collection color
     * else assign random color
     */
    col2 = !collectionColors.includes(collection.Collection)
      ? "#" + Math.floor(Math.random() * 16777215).toString(16)
      : collectionColors.find(
          (el) => el[0] == collection.Collection
        )[3];

    /** ASSIGN LANGUAGE COLOR
     * if collection colors includes the language (lang color has already been generated), find the first row that contains that language and pull its language color
     * else assign random color
     */
    langCol = !collectionColors.includes(Array.from(collection.Languages)[0])
      ? "#" + Math.floor(Math.random() * 16777215).toString(16)
      : collectionColors.find(
          (el) => el[1] == Array.from(collection.Languages)[0]
        )[4];
    
    /** TODO: ASSIGN LICENSE COLOR (BLOCK - NEED license purpose) */

    append(collectionColors, [
      collection.Collection, //0 - collection name
      Array.from(collection.Languages)[0], //1 - collection primary language
      "academic", //2 - license purpose
      col2, //3 - collection color
      langCol, //4 - language color
      "#00A3FF", //5 - license color
    ]);
  });

  //assign collectionColor, attrColor, licenseColor, name, collection

  collectionTable = new p5.Table();
  collectionTable.addColumn("name");
  collectionTable.addColumn("collection");
  collectionTable.addColumn("collectionColor");
  collectionTable.addColumn("languageColor");
  collectionTable.addColumn("licenseColor");

  collections.forEach((collection) => {
    let newRow = collectionTable.addRow();
    //newRow.setString('name', collection);
    newRow.setString("name", collection["Unique Dataset Identifier"]);
    newRow.setString("collection", collection.Collection);
    newRow.setString(
      "collectionColor",
      collectionColors.find((el) => el[0] == collection.Collection)[3]
    );
    newRow.setString(
      "languageColor",
      collectionColors.find((el) => el[0] == collection.Collection)[4]
    );
    newRow.setString(
      "licenseColor",
      collectionColors.find((el) => el[0] == collection.Collection)[5]
    );
  });
  
  // console.log(collectionTable);
}

function setupVis() {
  //initial drawing of display, set static attributes
  background("#151414");
  var x = xstart;
  var y = ystart;
  push();

  //draw bars by looping through collection table
  for (i = 0; i < collectionTable.getRowCount(); i++) {
    //name, collection, collectionColor, languageColor, licenseColor
    var t = new bar(
      x,
      y,
      random(20, 100),
      collectionTable.get(i, "collectionColor"),
      collectionTable.get(i, "languageColor"),
      collectionTable.get(i, "licenseColor"),
      collectionTable.get(i, "name"),
      collectionTable.get(i, "collection")
    );
    append(datasetBars, t);
    y += barHeight + yspacing;
    if (y > height - 100) {
      y = ystart;
      x += barWidth + xspacing;
    }
  }

  //dummy data bars
  // for (i = 1; i < 1000; i++) {
  //   var t = new bar(
  //     x,
  //     y,
  //     random(20, 100),
  //     color("#5E666B"),
  //     color("#F50A18"),
  //     color("#FFEB36"),
  //     "Dataset2",
  //     "Collection"
  //   );
  //   append(datasetBars, t);
  //   y += barHeight + yspacing;
  //   if (y > height - 100) {
  //     y = ystart;
  //     x += barWidth + xspacing;
  //   }
  // }
  pop();
}

function displayInteraction() {
  //continuously hook interaction
  for (let i = 0; i < datasetBars.length; i++) {
    datasetBars[i].detect(mouseX, mouseY);
    datasetBars[i].display();
  }
}

class bar {
  constructor(
    x,
    y,
    bwidth,
    collectionColor,
    attrColor,
    licenseColor,
    name,
    collection
  ) {
    this.x = x;
    this.y = y;
    this.defaultWidth = bwidth;
    this.w = bwidth;
    this.hover = false;
    this.name = name;
    this.collection = collection;
    this.col = collectionColor; //color("#5E666B");
    this.aCol = attrColor; //attribute (language, etc)
    this.lCol = licenseColor; //academic, commercial, etc...
    this.grow = false;
  }

  display() {
    //dataset line with license indicator
    if (this.hover) {
      //attribute color (bright)
      fill(this.aCol);
      this.w = this.defaultWidth + 20;

      //identifiers
      push();
      fill(255);
      rectMode(CORNER);
      text(`${this.name} | ${this.collection}`, this.x, this.y - yspacing / 2);
      pop();

      //indicator (additional attribute like license?)

      //TODO: if license exists
      push();
      fill(this.lCol);
      circle(this.x - 10, this.y + barHeight / 2, 5);
      pop();
    } else {
      //attribute color
      fill(red(this.aCol), green(this.aCol), blue(this.aCol), 150);
      this.w = this.defaultWidth;
    }

    let hold = this.w;
    if (isStandardState) {
      this.w = 100;
      push();
      fill(this.lCol);
      circle(this.x - 10, this.y + barHeight / 2, 5);
      pop();
      fill(red(this.col), green(this.col), blue(this.col), 150);
      if (this.hover) {
        fill(this.col);
      }
    } else {
      this.w = hold;
    }
    rect(this.x, this.y, this.w, barHeight, 5);
  }

  detect(detectX, detectY) {
    this.hover = false;
    if (
      detectX > this.x &&
      detectX <= this.x + this.w &&
      detectY > this.y &&
      detectY <= this.y + barHeight
    ) {
      this.hover = true;
    }
  }
}

function keyPressed() {
  //switch states
  if (keyCode === ENTER) {
    isStandardState = !isStandardState;
  }
}

//TODO*: simple state where all colors toggled off (monochrome)
//TODO*: numbers/percentages to supplement image
//TODO*: on click full dataset meta appears for the selected bar
//TODO: filtering by various attributes
//TODO*: visualize domain
//TODO*: underlying Licenses vs derivative licenses (trees?)
//TODO*: harmonize color
