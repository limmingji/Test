NewsNow Summarizer
==================

A lightweight command-line app that extracts headlines from NewsNow and produces
summaries of the linked stories.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python app.py --limit 5 --summary-sentences 3
```

You can also point the script at a specific NewsNow topic page:

```bash
python app.py --url "https://www.newsnow.com/us/" --limit 3
```

## Notes

- News sites change HTML structure frequently. If no headlines are found, try a
  different NewsNow page or adjust the scraping logic in `app.py`.
- This script is for learning and demo purposes; respect the website's terms of
  use and robots.txt.
