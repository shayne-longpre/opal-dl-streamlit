let Plot;
import("https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm").then(module => {
  Plot = module;
  // Your code that uses Plot here

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
  
  const mapPlot = createLanguageWorldMap(formattedCountryLanguageCount, countries, countrymesh, "Language Distribution", countryToLanguageMappingSingle)
  mapPlot.setAttribute("id", "language distribution worldmap")
  
  document.querySelector('#container').append(mapPlot)
  
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