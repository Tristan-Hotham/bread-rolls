# Barm, bap, cob or roll?

Mapping Britain's bread roll lines from 20,000 survey answers. Where the UK says roll, bun, bap, barm, cob, breadcake, teacake, muffin or batch: 20,038 answers from two dialect surveys, smoothed into the lines where one word gives way to another, checked against each other, against YouGov's 2018 county figures and against Wikipedia, and compared with the names of 614,437 food businesses.

**Interactive version:** https://tristan-hotham.github.io/bread-rolls/

**Paper:** https://doi.org/10.5281/zenodo.23691943

This repository holds the interactive page, aggregate data and the analysis code for the data study *Barm, bap, cob or roll? Mapping Britain's bread roll lines from 20,000 survey answers* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Companion study: [Beck, brook or burn](https://tristan-hotham.github.io/dale-down-fell-beck/).

## Headline results

- Roll is the national default: 46% of 20,038 answers, then bun 15%, bap 13%, barm 9% and cob 7%.
- South of a line from Cardigan Bay to the Lincolnshire coast, roll has a majority almost everywhere. Only 40% of English answers come from places where roll has a majority, against 93% in Scotland. In Northern Ireland 88% of answers say bap.
- Regional words lead in clear blocks: cob in the East Midlands, barm around Manchester and Liverpool, muffin east of Manchester, breadcake around Sheffield and Hull, bun up the north-east, bap in north Wales, Staffordshire and Northern Ireland, batch around Coventry.
- The two surveys agree closely on where each word is strong: county-level correlations of 0.99 (barm), 0.98 (breadcake), 0.95 (bun), 0.95 (cob), 0.68 (bap) across 44 counties.
- Our Dialects falls inside YouGov's published band for 18 of 32 county statements and within ten points for 7 more.
- In the cob heartland, 42% of Dialect and Heritage answers from under 25s say cob, against 61% at 45 to 64 (odds ratio 1.11 per decade of age, p = 0.04). No clear age slope for batch, barm or bun.
- Business names are a thin signal: 461 of 614,437 FSA businesses use a roll word, and only 3 use barm. Cob is the exception: 38 of 68 distinct cob names are in Derbyshire, Leicestershire and Nottinghamshire, which hold 4.7% of food businesses. Butty is a North West name: 45% of butty names are in five North West counties with 11% of businesses.

## Files

- `index.html`: the interactive page (Leaflet map, charts). `map/`: the smoothed overlays used by the map and the small-multiple image.
- `header.png`: social card.
- `data/survey_hexes.geojson`: answers by word in 20 km hexagons, only hexagons with at least 10 answers (318 hexagons, 95% of answers).
- `data/survey_counties.csv`: shares by word for each county, for both surveys separately and pooled, only where a county has at least 10 answers.
- `data/roll_lines.geojson`: the smoothed lines where the leading word changes, and the line where roll falls below half.
- `data/roll_word_matches.csv`: every business name (FSA and OpenStreetMap) that contains a roll or sandwich word, with whether it was kept and why not.
- `data/business_counties.csv`: kept business names by word and county, with the number of FSA businesses per county.
- `data/counties.geojson`: simplified county outlines (England ceremonial counties, Welsh preserved counties, Scottish council areas, Northern Ireland).
- `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `code/`: Python scripts, run in order: `01_prepare.py` (business names), `02_audit.py` (prints every match for checking), `03_analyse.py` (surveys, smoothing, lines, checks), `04_site_assets.py`, `05_build_site.py`, `06_figures.py`, `07_header.py`. `words.py` holds the word patterns and exclusion rules; `style.py` the palette. `release/paper/build_paper.py` writes and builds the paper; `release/build_release.py` the blog post and Zenodo files; `reddit/collage.py` the collage.

## Method in brief

Survey answers were placed in counties and counted on a 2 km grid by word, then smoothed with a Gaussian kernel. Kernel width: 8 km, chosen by leave-one-cell-out prediction, widened to 12, 16, 24 or 32 km where fewer than 10 weighted answers were nearby; cells still short were left blank. Lines are where the two leading words have equal shares, and where roll's share is one half. "Bread roll" and "roll" in Dialect and Heritage are counted together. Business names were searched for whole words and every match for the rarer words was read by eye; exclusion rules with reasons are in `code/words.py`.

Caveats: both surveys are volunteer online questionnaires, not samples; they used different pictures and options; one answer per person flattens people who use two words; Dialect and Heritage covers England only and Our Dialects has few answers from Scotland, Wales and Northern Ireland. Business names are often puns.

## Sources and licences

- Survey answers: [Our Dialects](https://www.ourdialects.uk/maps/bread/) bread map, © the Our Dialects project; [The Great Big Dialect Hunt: Roll with it](https://dialectandheritage.org.uk/the-great-big-dialect-hunt-the-results-are-in/food-glorious-food/roll-with-it/), © Dialect and Heritage Project, University of Leeds. Read from the projects' published web maps on 27 October 2026 and used for aggregate analysis with credit. **The individual answers are not included in this repository** and are not openly licensed; please use the projects' own maps.
- YouGov Profiles, [Cobs, buns, baps or barm cakes: what do people call bread rolls?](https://yougov.com/en-gb/articles/21204-cobs-buns-baps-or-barm-cakes-what-do-people-call-b), Matthew Smith, 20 July 2018 (published figures quoted).
- Foodhub app survey reported by the [Yorkshire Post](https://www.yorkshirepost.co.uk/read-this/the-nations-favourite-name-for-chips-and-bread-revealed-what-do-you-call-it-2968497), 11 September 2020 (published figures quoted).
- Food Standards Agency, Food Hygiene Rating Scheme open data, all local authorities, extract of 23 October 2026 (Open Government Licence v3.0).
- OpenStreetMap: named shop=bakery, amenity=cafe and amenity=fast_food in the UK, via QLever, 27 October 2026. © OpenStreetMap contributors, ODbL.
- County boundaries: Office for National Statistics (OGL v3.0), via the [How Roman is your road?](https://tristan-hotham.github.io/how-roman-is-your-road/) project. Contains OS data © Crown copyright and database right 2026.
- English Wikipedia articles Barm cake, List of bread rolls, Teacake, Bun and Morning roll, retrieved 27 October 2026 (CC BY-SA 4.0).
- Inspiration: Le Baguette Index, [La Ligne Chocolatine](https://lebaguetteindex.fr/chocolatine/).
- Base map tiles on the page © Esri. Map library: Leaflet.

My derived aggregates, map images and text are released under CC BY 4.0, with the credits above. The business-name list also contains OpenStreetMap data (ODbL) and FSA data (OGL v3.0). Code is MIT (see `LICENSE`).

## Rerun

Needs Python 3 with numpy, pandas, scipy, shapely, pyproj, scikit-image, statsmodels, matplotlib and Pillow (Playwright for the header). The source files are read in place from a sibling folder `../_data10/` (see the paths at the top of each script); the survey files must be obtained from the projects.

## Citation

Hotham, T. (2026). *Barm, bap, cob or roll? Mapping Britain's bread roll lines from 20,000 survey answers*. Zenodo. https://doi.org/10.5281/zenodo.23691943

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
