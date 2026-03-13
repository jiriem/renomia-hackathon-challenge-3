# Challenge 3: Nacenění aut - speciální vozidla (Vehicle Pricing >3.5t)

Estimate the current market value of heavy/special vehicles (trucks, trailers, construction equipment) based on vehicle details, backed by real market data.

## What you need to do

Implement the `solve()` function in `main.py`. Your endpoint receives vehicle identification details and must return a price estimate with at least 3 supporting sources (real market listings).

## Input format

```json
POST /solve
{
  "make": "MAN",
  "model": "TGX 18.510 4x2",
  "year": 2020,
  "mileage_km": 320000,
  "body_type": "chladírenská nástavba",
  "additional_info": "Euro 6, BLS, retarder"
}
```

### Input fields

| Field | Type | Description |
|-------|------|-------------|
| `make` | string | Manufacturer (MAN, Scania, Volvo, DAF, Mercedes-Benz, Iveco, ...) |
| `model` | string | Model designation |
| `year` | number | Year of manufacture |
| `mileage_km` | number | Odometer reading in km |
| `body_type` | string | Body type / superstructure (Czech) |
| `additional_info` | string | Additional specs (emission class, features, etc.) |

### Matching priority (most to least important)

1. **Make + Model** (Tovární značka + Model)
2. **Body type** (Typ nástavby)
3. **Year of manufacture** (Rok výroby)
4. **Mileage** (Najeté km)

## Expected output

```json
{
  "estimated_value_czk": 1450000,
  "currency": "CZK",
  "price_range_czk": {
    "min": 1200000,
    "max": 1700000
  },
  "sources": [
    {
      "url": "https://www.truck1.eu/construction-machinery/...",
      "title": "MAN TGX 18.510, 2020, chladírenská",
      "price": 52000,
      "currency": "EUR",
      "price_czk": 1300000
    },
    {
      "url": "https://www.autoline.info/-/sale/used-trucks/...",
      "title": "MAN TGX 18.510 4x2 BLS",
      "price": 55000,
      "currency": "EUR",
      "price_czk": 1375000
    },
    {
      "url": "https://www.tipcars.com/nakladni-auto/...",
      "title": "MAN TGX 18.510",
      "price": 1500000,
      "currency": "CZK",
      "price_czk": 1500000
    }
  ],
  "methodology": "Averaged 3 listings from truck1.eu, autoline.info, tipcars.com"
}
```

### Output fields

| Field | Type | Description |
|-------|------|-------------|
| `estimated_value_czk` | number | Your best estimate in CZK |
| `currency` | string | Always `"CZK"` |
| `price_range_czk.min` | number | Lower bound estimate (CZK) |
| `price_range_czk.max` | number | Upper bound estimate (CZK) |
| `sources` | array | At least 3 real market listings |
| `sources[].url` | string | URL of the listing |
| `sources[].title` | string | Listing title |
| `sources[].price` | number | Listed price in original currency |
| `sources[].currency` | string | Original currency (EUR, CZK, etc.) |
| `sources[].price_czk` | number | Price converted to CZK |
| `methodology` | string | Brief description of your pricing approach |

## Scoring

| Component | Weight | Details |
|-----------|--------|---------|
| Price accuracy | 50% | ±10% of expected = full score, decreases to ±50% |
| Sources | 25% | 3+ sources = full score, fewer = proportional |
| Price range | 15% | Expected value falls within your min-max range |
| Currency | 10% | Must be `"CZK"` |

## Local development

```bash
# Start the app + sidecar database
docker compose up --build

# Test your endpoint
curl -X POST http://localhost:8080/solve \
  -H "Content-Type: application/json" \
  -d '{
    "make": "Scania",
    "model": "R 450",
    "year": 2019,
    "mileage_km": 450000,
    "body_type": "tahač návěsů",
    "additional_info": "Euro 6, Retarder, Klimatizace"
  }'

# Check health
curl http://localhost:8080/

# Check token usage
curl http://localhost:8080/metrics
```

## Available tools

- **Gemini API** — use the pre-configured `gemini` object: `response = gemini.generate("your prompt")`. Token usage is tracked automatically. Gemini supports [Google Search grounding](https://ai.google.dev/gemini-api/docs/grounding) which can find real listings.
- **PostgreSQL sidecar** — available at `DATABASE_URL` for caching. A `cache` table (key TEXT, value JSONB) is created on startup.

## Deployment

Push to your GitHub repo — Cloud Build will automatically build and deploy to Cloud Run.

## Tips

- **Gemini with Google Search grounding** is the easiest way to find real truck listings — it can search the web and return URLs
- Useful marketplaces: truck1.eu, autoline.info, mobile.de, tipcars.com, mascus.com
- For EUR→CZK conversion, use approximately 25 CZK/EUR (or fetch the current rate)
- Cache results in the sidecar DB — the same vehicle may be queried multiple times
- Body types are in Czech: "tahač návěsů" (tractor), "valníková nástavba" (flatbed), "chladírenská nástavba" (refrigerated), "skříňová nástavba" (box body), "cisterna" (tanker), "nosič kontejnerů" (container carrier)
- If you can't find an exact match, look for similar vehicles and adjust for year/mileage differences
- Prices vary significantly by body type — a refrigerated truck is worth more than a bare chassis
