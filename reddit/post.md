# Reddit post

## Title

[OC] Barm, bap, cob or roll? Where the UK's words for a bread roll give way to each other, from 20,038 answers in two dialect surveys (and why shop names barely show it)

## Body

I combined the answers from two dialect surveys (Our Dialects and the University of Leeds Dialect and Heritage Project), smoothed them, and drew the lines where the leading word changes. Roll is 46% of all answers and holds the south and Scotland, but north of a line from Cardigan Bay to the Lincolnshire coast it splits into cob, barm, breadcake, bun, bap, teacake, muffin and batch. In Northern Ireland 88% say bap. The two surveys agree closely on where each word lives (county correlation 0.99 for barm). Caveat: these are volunteer surveys, not samples, with few answers outside England. I also searched 614,437 food business names: only 3 use barm, but cob shops really do cluster in the East Midlands.

Interactive version: https://tristan-hotham.github.io/bread-rolls/

## Source comment

Source: Our Dialects bread map (https://www.ourdialects.uk/maps/bread/, copyright the Our Dialects project) and the Dialect and Heritage Project, University of Leeds, "Roll with it" (https://dialectandheritage.org.uk/the-great-big-dialect-hunt-the-results-are-in/food-glorious-food/roll-with-it/, copyright the project); both used with credit for aggregate analysis only, individual answers not republished. YouGov Profiles 2018 county figures (published). Food Standards Agency Food Hygiene Rating Scheme open data, all local authorities, October 2026 (Open Government Licence v3.0). OpenStreetMap named bakeries, cafes and fast food (ODbL). ONS county boundaries (OGL v3.0, contains OS data © Crown copyright and database right 2026).

Tools: Python (pandas, NumPy, SciPy, shapely, pyproj, scikit-image, statsmodels, matplotlib). Smoothing: Gaussian kernel, 8 km where answers are dense (chosen by cross-validation), widened up to 32 km where sparse; areas with fewer than 10 weighted answers left blank.

Interactive version: https://tristan-hotham.github.io/bread-rolls/
Blog post: https://blog.tristanhotham.com/2026/10/27/bread-rolls/
Paper: https://doi.org/10.5281/zenodo.23691943
