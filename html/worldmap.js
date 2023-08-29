let Plot;
import("https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm").then(module => {
  Plot = module;
  // Your code that uses Plot here


  // let dataSummary;

  // function preload() {
  //   // load collections
  //   dataSummary = JSONDATA;
  // }

  // dataSummary = JSONDATA;

  async function readJsonData(filePath) {
    try {
      let response = await fetch(filePath);

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching data:', error);
      throw error;
    }
  }

  let licenseClassRemapper = {
    "commercial": "Commercial",
    "unspecified": "Unspecified",
    "non-commercial": "Non-Commercial/Academic",
    "academic-only": "Non-Commercial/Academic",
    "unclear": "Non-Commercial/Academic",
  };

  function roundToOneDecimalPlace(number) {
    return Math.round(number * 10) / 10;
  }

  function prepareDataSummary(data) {
    // CLEAN/FORMAT THE DATA
    const ddata = Object.values(data);

    // Map the dataset name to its object to easily find and update it
    let accumulatedLanguages = {};
    ddata.forEach((dataset) => {
      const datasetName = dataset["Dataset Name"];
      if (!accumulatedLanguages[datasetName]) {
        accumulatedLanguages[datasetName] = [];
      }
      accumulatedLanguages[datasetName].push(...dataset.Languages)
    });

    let clean = [];
    let seenNames = new Set();
    ddata.forEach((dataset) => {
      const datasetName = dataset["Dataset Name"];

      // Check if dataset name is already seen, if so skip this iteration
      // This is for variants of the same dataset which may have different languages
      // but not different tasks, topics, or other metadata.
      if (seenNames.has(dataset["Dataset Name"])) return;

      // Otherwise, add the name to the set
      seenNames.add(dataset["Dataset Name"]);

      // If we haven't seen this dataset name yet, process it fully as before
      var obj = {};
      obj['datasetName'] = datasetName;
      obj['collection'] = dataset.Collection;
      obj['languages'] = accumulatedLanguages[datasetName];
      obj['tasks'] = Array.from(dataset["Task Categories"]);
      obj['textSources'] = Array.from(dataset["Text Sources"]);
      obj['textDomains'] = Array.from(dataset["Text Domains"]);
      obj['creators'] = Array.from(dataset["Creators"]);

      obj['licenseUseClass'] = dataset["License Use (DataProvenance)"];
      obj['licenseUseCategory'] = licenseClassRemapper[dataset["License Use (DataProvenance)"]] || dataset["License Use (DataProvenance)"];
      obj['synthetic'] = Array.from(dataset["Model Generated"]).length > 0 ? "Synthetic" : "Regular";

      const models = ["OpenAI GPT-3", "OpenAI ChatGPT", "OpenAI GPT-4", "OpenAI Codex"];
      if (Array.from(dataset["Model Generated"]).length > 0) {
        if (models.includes(dataset["Model Generated"][0])) {
          obj['syntheticClass'] = "Synthetic (" + dataset["Model Generated"][0] + ")";
        } else {
          obj['syntheticClass'] = "Synthetic (Other)";
        }
      } else {
        obj['syntheticClass'] = "Regular";
      }


      obj['textTopics'] = dataset?.["Inferred Metadata"]?.["Text Topics"] ?? [];

      obj['cd_frequency'] = 0; // frequency of citation count, download count pair
      obj['citationCount'] = dataset?.["Inferred Metadata"]?.["S2 Citation Count (June 2023)"] ?? 0;
      obj['downloadCount'] = dataset?.["Inferred Metadata"]?.["HF Downloads (June 2023)"] ?? 0;

      obj['inputTextLen'] = roundToOneDecimalPlace(dataset?.["Text Metrics"]?.["Mean Inputs Length"]) ?? 0;
      obj['targetTextLen'] = roundToOneDecimalPlace(dataset?.["Text Metrics"]?.["Mean Targets Length"]) ?? 0;

      obj['pwcDate'] = dataset?.["Inferred Metadata"]?.["PwC Date"] ?? "1900-1-1";
      obj['ssDate'] = dataset?.["Inferred Metadata"]?.["S2 Date"] ?? "1900-1-1";
      obj['date'] = new Date(obj['pwcDate'] < obj['ssDate'] ? obj['pwcDate'] : obj['ssDate'])

      obj["hfLink"] = dataset["Hugging Face URL"];

      // Add the dataset object to our map
      seenNames[datasetName] = obj;

      clean.push(obj);
    });
    return clean;
  }


  function setupLangWorldMap(countryCodes, langCodes, countryCodeToLangCodes) {

    const langMap = {};
    for (const code in langCodes) {
      langMap[code] = langCodes[code].split(';').map(lang => lang.trim());
    }

    // Create the desired output mapping from country name to their languages and percentages
    const countryToLanguageMapping = {};

    for (let country of countryCodes) {
      const { code, name } = country;

      const languageDataForCountry = countryCodeToLangCodes[code];
      if (!languageDataForCountry) continue;  // Skip countries without language data

      countryToLanguageMapping[name] = {};

      for (let langCode in languageDataForCountry) {
        const { percent } = languageDataForCountry[langCode];
        const languageNames = langMap[langCode];

        if (languageNames) {
          for (let langName of languageNames) {
            countryToLanguageMapping[name][langName] = percent / 100.0;
          }
        }
      }
    }

    // Step 1: Map language to countries present for easy lookup
    const languageToCountryMapping = {};
    for (let country in countryToLanguageMapping) {
      for (let lang in countryToLanguageMapping[country]) {
        if (lang in countryToLanguageMapping[country] > 0.1) {
          if (!languageToCountryMapping[lang]) {
            languageToCountryMapping[lang] = [];
          }
          languageToCountryMapping[lang].push(country);
        }
      }
    }
    return languageToCountryMapping;
  }

  function createWorldMap(counts, countries, countrymesh, title) {
    // Create a map with country names as keys and their respective values
    const countryValueMap = new Map(counts.map(d => [d.name, d.value]));

    return Plot.plot({
      projection: "equal-earth",
      width: 928,
      height: 928 / 2,
      color: { scheme: "YlGnBu", unknown: "#ccc", label: title, legend: true },
      marks: [
        Plot.sphere({ fill: "white", stroke: "currentColor" }),
        Plot.geo(countries, {
          fill: d => countryValueMap.get(d.properties.name),
          title: (d) => {
            const value = countryValueMap.get(d.properties.name);
            return `Country: ${d.properties.name}, Value: ${value}`;
          }
        }),
        Plot.geo(countrymesh, { stroke: "white" }),
      ]
    });
  }

  function createWorldMap1(counts, countries, countrymesh, title, countryToLanguageMapping) {
    // Create a map with country names as keys and their respective values
    const countryValueMap = new Map(counts.map(d => [d.name, d.value]));

    return Plot.plot({
      projection: "equal-earth",
      width: 928,
      height: 928 / 2,
      color: { scheme: "YlGnBu", unknown: "#ccc", label: title, legend: true },
      marks: [
        Plot.sphere({ fill: "white", stroke: "currentColor" }),
        Plot.geo(countries, {
          fill: d => countryValueMap.get(d.properties.name),
          title: (d) => {
            const countryName = d.properties.name;
            const value = countryValueMap.get(countryName);
            let languageStr = "";

            const languageMapping = countryToLanguageMapping[countryName];
            if (languageMapping) {
              for (const [lang, proportion] of Object.entries(languageMapping)) {
                if (proportion >= 0.05) { // 10% threshold
                  languageStr += `${lang} (${(proportion * 100).toFixed(0)}%), `;
                }
              }
              // Removing trailing comma and space
              languageStr = languageStr.slice(0, -2);
            }

            return `Country: ${countryName}\n${languageStr ? `Spoken Languages: ${languageStr}` : ''}`;
          }
        }),
        Plot.geo(countrymesh, { stroke: "white" }),
      ]
    });
  }

  var countries = topojson.feature(world, world.objects.countries)
  var countrymesh = topojson.mesh(world, world.objects.countries, (a, b) => a !== b)


  const languageToCountryMapping = setupLangWorldMap(countryCodes, langCodes, countryCodeToLangCodes)

  const langMap = {};
  for (const code in langCodes) {
      langMap[code] = langCodes[code].split(';').map(lang => lang.trim());
  }
  
  // Create the desired output mapping from country name to their languages and percentages
  const countryToLanguageMapping = {};
  const countryToLanguageMappingSingle = {};
  
  for (let country of countryCodes) {
      const { code, name } = country;
  
      const languageDataForCountry = countryCodeToLangCodes[code];
      if (!languageDataForCountry) continue;  // Skip countries without language data
  
      countryToLanguageMapping[name] = {};
      countryToLanguageMappingSingle[name] = {};
  
      for (let langCode in languageDataForCountry) {
          const { percent } = languageDataForCountry[langCode];
          const languageNames = langMap[langCode];
  
          if (languageNames && languageNames.length > 0) {
              // Use only the first language name for each language code
              const langName = languageNames[0];
              countryToLanguageMappingSingle[name][langName] = percent / 100.0;
          }
  
          if (languageNames) {
              for (let langName of languageNames) {
                  countryToLanguageMapping[name][langName] = percent / 100.0;
              }
          }
      }
  }
  
  // console.log(countryToLanguageMapping)
  
  const clean = prepareDataSummary(dataSummary)
  
  // Step 2: Iterate through the `clean` list
  const countryLanguageCount = {};
  const unmatchedLanguages = new Set(); // Using a Set to avoid duplicate entries
  
  for (let item of clean) {
      const languagesInItem = item.languages;
  
      for (let lang of languagesInItem) {
          // if (lang === "Russian") {
          //     console.log(languageToCountryMapping[lang])
          //     console.log(countryToLanguageMapping["Russian Federation"][lang])
          // }
          if (lang in languageToCountryMapping) {
              for (let country of languageToCountryMapping[lang]) {
                  // countryToLanguageMapping[country] = (countryToLanguageMapping[country] || 0) + 1;
                  countryLanguageCount[country] = (countryLanguageCount[country] || 0) + countryToLanguageMapping[country][lang];
              }
          } else {
              unmatchedLanguages.add(lang);
          }
      }
  }
  
  const maxVal = Math.max(...Object.values(countryLanguageCount));
  // Format countryLanguageCount as a list of dictionaries
  const formattedCountryLanguageCount = Object.keys(countryLanguageCount).map(country => ({
      name: country,
      value: countryLanguageCount[country] / maxVal
  }));
  
  const mapPlot = createWorldMap1(formattedCountryLanguageCount, countries, countrymesh, "Language Distribution", countryToLanguageMappingSingle)
  mapPlot.setAttribute("id", "language distribution worldmap")
  
  document.querySelector('#container').append(mapPlot)
  
  //     Plot.plot({
  //         projection: "equal-earth",
  //         width: 928,
  //         height: 928 / 2,
  //         color: {scheme: "YlGnBu", unknown: "#ccc", label: "Language Distribution", legend: true},
  //         marks: [
  //         Plot.sphere({fill: "white", stroke: "currentColor"}),
  //         Plot.geo(countries, {
  //             fill: (map => d => map.get(d.properties.name))(new Map(formattedCountryLanguageCount.map(d => [d.name, d.value]))),
  //         }),
  //         Plot.geo(countrymesh, {stroke: "white"}),
  //     ]
  //     })
  // )
  
  
  // Extract mesh country names for debugging:
  const mesh_countries_list = new Set();
  for (let feature of countries.features) {
      mesh_countries_list.add(feature.properties.name)
  }
  
  const unseen_countries = new Set();
  for (let country of formattedCountryLanguageCount) {
      if (!mesh_countries_list.has(country.name)) {
          unseen_countries.add(country.name)
      }
  }

});