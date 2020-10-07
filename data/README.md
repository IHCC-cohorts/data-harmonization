# Source Data

- `member_cohorts.csv` contains metadata for all IHCC cohorts retrieved from their [Member Cohorts](https://ihcc.g2mc.org/membercohorts/)
- `cineca.tsv` is a TSV version of [WP3.1 Base material for cohort minimal meta data model](https://docs.google.com/spreadsheets/d/1ZXqTMIhFtGOaodw7Fns5YghvY_pWos-RuSa2BFnO5l4)
- `genomics-england.xlsx` is an Excel spreadsheet containing the [Genomics England Main Programme Data](https://cnfl.extge.co.uk/pages/viewpage.action?pageId=113189195)
- `golestan-cohort-study.xlsx` is an Excel spreadsheet containing the [data dictionary](https://drive.google.com/file/d/1ZLw-D6AZFKrBjTNsc4wzlthYq4w4KmOJ/view) for the Golestan Cohort Study — a prospective study of oesophageal cancer in northern Iran
- `koges.tsv` is a TSV version of [KoGES collected variables](https://drive.google.com/file/d/1Hh_cG9HcZWXs70FEun8iDZZbt0H_J1oq/view) for the [Korean Genome and Epidemiology Study](http://www.cdc.go.kr/contents.es?mid=a50401010100) - the spreadsheet can be found [here](https://docs.google.com/spreadsheets/d/1hPcCzjFWHJ7iiqMHBpuodFCrrTvSmCKfQu0f93JPhU8/edit?usp=sharing)
- `maelstrom.yml` is a YAML version of [Maelstrom Area of Information taxonomy](https://github.com/maelstrom-research/maelstrom-taxonomies)
- `saprin.tsv` is a TSV version of [SAPRIN Core Data Elements](https://drive.google.com/file/d/1u1sXEAAU7N_n2-WqfF6lMJozVVQSI0EU) - the spreadsheet can be found [here](https://docs.google.com/spreadsheets/d/1KjULwQ38IkWqJxOCZZ2em8ge7NZJEngOZqI3ebC9Wkk/edit?usp=sharing)
- `vukuzazi.xlsx` is an Excel spreadsheet containing the northern KwaZulu-Natal - South Africa Interactions between HIV, tuberculosis (TB), environmental exposures and non-communicable diseases data dictionary

# Generated Data

- `cohort-data.json` contains each cohort that has been converted to OWL and mapped to GECKO (includes details `member_cohorts.csv` and upper-level GECKO categories that are included in the cohort data dictionary)
- `random-data.json` contains the same details (with randomly-generated GECKO categories) for all cohorts from `member_cohorts.csv` that have **not** been converted to OWL
- `full-cohort-data.json` combines `cohort-data.json` and `random-data.json` for use in the IHCC browser demo
- `ols-config.yaml` contains the configuration file for the IHCC OLS instance (https://registry.ihccglobal.app/index)
- `ihcc-mapping-suggestions-zooma.tsv` contains the mapping database that is loaded into the [IHCC Zooma instance](https://mapping.ihccglobal.app/zooma/)