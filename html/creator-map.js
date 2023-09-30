let Plot;
import("https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm").then(module => {
    Plot = module;
    // Your code that uses Plot here

    var countries = topojson.feature(world, world.objects.countries)
    var countrymesh = topojson.mesh(world, world.objects.countries, (a, b) => a !== b)

    const creatorToCountry = {};
    for (let country in countryToCreator) {
        for (let creator of countryToCreator[country]) {
            if (!creatorToCountry[creator]) {
                creatorToCountry[creator] = [];
            }
            creatorToCountry[creator].push(country)
        }
    }

    const clean = prepareDataSummary(dataSummary)

    // Iterate through the `clean` list
    const countryToCreatorMapping = {};
    const unmatchedCreators = new Set(); // Using a Set to avoid duplicate entries

    for (let item of clean) {
        const creatorsInItem = item.creators;

        for (let creator of creatorsInItem) {
            if (creator in creatorToCountry) {
                for (let country of creatorToCountry[creator]) {
                    countryToCreatorMapping[country] = (countryToCreatorMapping[country] || 0) + 1;
                    // countryLanguageCount[country] = (countryLanguageCount[country] || 0) + countryToLanguageMapping[country][lang];
                }
            } else {
                unmatchedCreators.add(creator);
            }
        }
    }

    // console.log(countryLanguageCount)

    // Format countryLanguageCount as a list of dictionaries
    const maxVal = Math.max(...Object.values(countryToCreatorMapping));
    const formattedCountryCreatorCount = Object.keys(countryToCreatorMapping).map(country => ({
        name: country,
        value: countryToCreatorMapping[country] / maxVal
    }));

    // console.log("testtttt")
    // console.log(formattedCountryCreatorCount)
    const mapPlot = createWorldMap(formattedCountryCreatorCount, countries, countrymesh, "Creator Distribution")
    mapPlot.setAttribute("id", "creator distribution worldmap")


    document.querySelector('#container').append(mapPlot)

    // Print the unmatched languages
    // console.log("Unmatched creators:", [...unmatchedCreators]);

});