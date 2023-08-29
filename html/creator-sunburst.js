let Plot;
import("https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm").then(module => {
    Plot = module;
    // Your code that uses Plot here


    function sunburst(data, name) {
        // Specify the chart’s dimensions.
        const width = 928;
        const height = width;
        const radius = width / 6;

        // Create the color scale.
        const color = d3.scaleOrdinal(d3.quantize(d3.interpolateRainbow, data.children.length + 1));

        // Compute the layout.
        const hierarchy = d3.hierarchy(data)
            .sum(d => d.value)
            .sort((a, b) => b.value - a.value);
        const root = d3.partition()
            .size([2 * Math.PI, hierarchy.height + 1])
            (hierarchy);
        root.each(d => d.current = d);

        // Create the arc generator.
        const arc = d3.arc()
            .startAngle(d => d.x0)
            .endAngle(d => d.x1)
            .padAngle(d => Math.min((d.x1 - d.x0) / 2, 0.005))
            .padRadius(radius * 1.5)
            .innerRadius(d => d.y0 * radius)
            .outerRadius(d => Math.max(d.y0 * radius, d.y1 * radius - 1))

        // Create the SVG container.
        const svg = d3.create("svg")
            // .attr("viewBox", [-width / 2, -height / 2, width, width])
            .attr("viewBox", [-width / 1.35, -height / 1.35, width * 1.5, width * 1.5])
            .style("font", "10px sans-serif");

        // Append the arcs.
        const path = svg.append("g")
            .selectAll("path")
            .data(root.descendants().slice(1))
            .join("path")
            .attr("fill", d => { while (d.depth > 1) d = d.parent; return color(d.data.name); })
            .attr("fill-opacity", d => arcVisible(d.current) ? (d.children ? 0.6 : 0.4) : 0)
            .attr("pointer-events", d => arcVisible(d.current) ? "auto" : "none")
            .attr("d", d => arc(d.current));

        // Make them clickable if they have children.
        path.filter(d => d.children)
            .style("cursor", "pointer")
            .on("click", clicked);

        const format = d3.format(",d");
        path.append("title")
            .text(d => `${d.ancestors().map(d => d.data.name).reverse().join("/")}\n${format(d.value)}`);


        var label = svg.append("g")
            .attr("pointer-events", "none")
            .attr("text-anchor", "middle")
            .style("user-select", "none")
            .selectAll("text")
            .data(root.descendants().slice(1))
            .join("text")
            .attr("font-size", function (d) {
                if (d.depth <= 1) {
                    return "1rem"
                }
                else { return "0.75rem" }
            })
            .attr("font-weight", function (d) {
                if (d.depth <= 1) {
                    return "bold"
                }
            })
            .attr("transform", function (d) {
                const x = (d.x0 + d.x1) / 2 * 180 / Math.PI;
                const y = (d.y0 + d.y1) / 2;
                return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
            })
            .attr("dy", "0.35em")
            .attr("fill-opacity", d => +labelVisible(d.current))
            .attr("transform", d => labelTransform(d.current))
            .text(d => {
                const textLength = d.data.name.length < 25 ? d.data.name : d.data.name.slice(0, 20) + '...';
                const percentage = ((d.value / root.value) * 100).toFixed(0) + "%";
                return `${textLength}`;
            //return `${textLength} (${percentage})`;
            });

        var pct_label = svg.append("g")
            .attr("pointer-events", "none")
            .attr("text-anchor", "middle")
            .style("user-select", "none")
            .selectAll("text")
            .data(root.descendants().slice(1))
            .join("text")
            .attr("font-size", function (d) {
                if (d.depth <= 1) {
                    return "1rem"
                }
                else { return "0.75rem" }
            })
            .attr("font-weight", function (d) {
                if (d.depth <= 1) {
                    return "bold"
                }
            })
            .attr("transform", function (d) {
                const x = (d.x0 + d.x1) / 2 * 180 / Math.PI;
                const y = (d.y0 + d.y1) / 2;
                return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
            })
            .attr("dy", "0.35em")
            .attr("fill-opacity", d => +labelPctVisible(d.current))
            // .attr("transform", d => d.depth === 1 ? 1 : 2)
            .attr("transform", d => labelPctTransform(d.current))
            .text(d => {
                const textLength = d.data.name.length < 25 ? d.data.name : d.data.name.slice(0, 20) + '...';
                const percentage = ((d.value / root.value) * 100).toFixed(1) + "%";
                return `${(percentage)}`;
            //return `${textLength} (${percentage})`;
            });

        const parent = svg.append("circle")
            .datum(root)
            .attr("r", radius)
            .attr("fill", "none")
            .attr("pointer-events", "all")
            .on("click", clicked);

        //*NEW* append percentage lists off to side
        // const allList = list(svg, 'Commercial', 350, 0)
        // const academicList = list(svg, 'Non-Commercial/Academic', 0, -425)
        // const nonComList = list(svg, 'non-commercial', -150, -425)
        // const unclearList = list(svg, 'Unspecified', -350, -100)

        //percentage lists
        function list(svg, parent, xtranslate, ytranslate) {
            let yy = -20;
            return svg.append("g")
                .attr("pointer-events", "none")
                .attr("text-anchor", "middle")
                .style("user-select", "none")
                .selectAll("text")
                .data(root.descendants().slice(1).filter(d => d.data.name == parent || (d.depth >= 2 && d.parent.data.name == parent)).slice(0, 10))
                .join("text")
                .attr("font-size", function (d) {
                    if (d.depth <= 1) {
                        return "1rem"
                    }
                    else { return "0.75rem" }
                })
                .attr("font-weight", function (d) {
                    if (d.depth <= 1) {
                        return "bold"
                    }
                })
                .attr("transform", function (d) {
                    yy += 20;
                    return d.depth >= 2 ? `translate(${arc.centroid(d.parent)[0] + xtranslate},${arc.centroid(d.parent)[1] + ytranslate + yy})` : `translate(${arc.centroid(d)[0] + xtranslate},${arc.centroid(d)[1] + ytranslate + yy})`
                })
                .text(d => {
                    // console.log(d)
                    const textLength = d.data.name.length < 20 ? d.data.name : d.data.name.slice(0, 14) + '...';
                    const percentage = ((d.value / root.value) * 100).toFixed(1) + "%";
                    return `${textLength} (${percentage})`;
                });
        }

        // Handle zoom on click.
        function clicked(event, p) {
            parent.datum(p.parent || root);

            root.each(d => d.target = {
                x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
                x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
                y0: Math.max(0, d.y0 - p.depth),
                y1: Math.max(0, d.y1 - p.depth)
            });

            const t = svg.transition().duration(750);

            // Transition the data on all arcs, even the ones that aren’t visible,
            // so that if this transition is interrupted, entering arcs will start
            // the next transition from the desired position.
            path.transition(t)
                .tween("data", d => {
                    const i = d3.interpolate(d.current, d.target);
                    return t => d.current = i(t);
                })
                .filter(function (d) {
                    return +this.getAttribute("fill-opacity") || arcVisible(d.target);
                })
                .attr("fill-opacity", d => arcVisible(d.target) ? (d.children ? 0.6 : 0.4) : 0)
                .attr("pointer-events", d => arcVisible(d.target) ? "auto" : "none")

                .attrTween("d", d => () => arc(d.current));

            label.filter(function (d) {
                // if (d.data.name === "Miscellaneous") console.log(d.current, d.target);
                return +this.getAttribute("fill-opacity") || labelVisible(d.target);
            }).transition(t)
                .attr("fill-opacity", d => +labelVisible(d.target))
                .attrTween("transform", d => () => labelTransform(d.current));


            pct_label.filter(function (d) {
                // if (d.data.name === "Misc.") console.log(d.current, d.target);
                return +this.getAttribute("fill-opacity") || labelPctVisible(d.target);
            }).transition(t)
                .attr("fill-opacity", d => +labelPctVisible(d.target))
                .attrTween("transform", d => () => labelPctTransform(d.current));

            // if (p.depth === 1) {
            //     pct_label.filter(function (d) {
            //         return +this.getAttribute("fill-opacity") || labelPctVisible(d.target);
            //     }).transition(t)
            //         .attr("fill-opacity", d => +labelPctVisible(d.target))
            //         .attrTween("transform", d => () => labelPctTransform(d.target));
            // } else {
            //     pct_label.filter(function (d) {
            //         return +this.getAttribute("fill-opacity") || labelPctVisible(d.target);
            //     }).transition(t)
            //         // .attr("fill-opacity", 0)
            //         .attr("fill-opacity", d => +labelPctVisible(d.target))
            //         .attrTween("transform", d => () => labelPctTransform(d.target));
            // }
        }
        

        function arcVisible(d) {
            return d.y1 <= 3 && d.y0 >= 1 && d.x1 > d.x0;
        }

        function labelVisible(d) {
            return d.y1 <= 3 && d.y0 >= 1 && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.03;
        }

        function labelPctVisible(d) {
            if (d.depth > 1) {
                return d.y1 <= 3 && d.y0 >= 1 && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.03;
            } else {
                return d.y1 <= 3 && d.y0 >= 1 && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.15;
            }
        }

        function labelTransform(d) {
            const x = (d.x0 + d.x1) / 2 * 180 / Math.PI;
            const y = (d.y0 + d.y1) / 2 * radius;
            return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
        }
        function labelPctTransform(d) {
            // console.log(d)
            const y_const = (d.depth > 1) ? 1.3 : -1.45;
            const x_const = (d.depth > 1) ? 0 : 0;
            const x = (d.x0 + d.x1 + x_const) / 2 * 180 / Math.PI;
            const y = (d.y0 + d.y1 + y_const) / 2 * radius;
            return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
        }

        svg.attr("id", name)
        return svg.node();
    }

    const clean = prepareDataSummary(dataSummary)
    // console.log(clean)
    // const nestedData = transformToNestedFormat(clean, 'licenseUseCategory', 'textTopics');

    // const hierarchyData = d3.hierarchy(nestedData)
    //     .sum(d => d.value)
    //     .sort((a, b) => b.value - a.value);

    // document.querySelector("#container").append(sunburst(nestedData))
    // document.querySelector("#container").append(sunburst(nestedData, "license sunburst"));


    // let taskData = convertToSunburstFormat(clean, TASK_GROUPS, "tasks");
    // document.querySelector("#container").append(sunburst(taskData, "tasks sunburst"));

    const creatorData = convertToSunburstFormat(clean, CREATOR_GROUPS, "creators");
    document.querySelector("#container").append(sunburst(creatorData, "creator sunburst"));

});