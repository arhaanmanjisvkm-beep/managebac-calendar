# managebac-calendar

Publishes a filtered `.ics` feed of summative assessments and major deadlines
pulled from a ManageBac calendar export, for subscribing to in Google Calendar.

Only `public/summatives.ics` is committed — event titles, times, and rooms.
No descriptions, no teacher notes, no ManageBac auth token.

## How it works

`sync.py` fetches the raw ManageBac calendar feed (URL kept in `config.json`,
gitignored), keeps only events whose title matches a summative/major-deadline
keyword (see `config.json`), strips everything but title/time/location, and
writes the result to `public/summatives.ics`.

## Usage

```bash
./venv/bin/python sync.py --dry-run   # preview what would be kept/dropped
./venv/bin/python sync.py             # write public/summatives.ics
git add public/summatives.ics && git commit -m "sync" && git push
```

A launchd job runs this on a schedule and pushes automatically — see
`com.arhaan.managebac-sync.plist`.

## Subscribing in Google Calendar

Google Calendar → Settings → Add calendar → From URL → paste the raw GitHub
URL for `public/summatives.ics`. Google polls it roughly every 12-24 hours.
