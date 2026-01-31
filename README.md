# 🇸🇬 SG Outdoor Guide

**Should you go outside?** Real-time conditions for Singapore.

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://sg-outdoor-guide.onrender.com)
[![Made in Singapore](https://img.shields.io/badge/made%20in-Singapore-red)](https://sg-outdoor-guide.onrender.com)

## 🎯 What Makes This Different?

Unlike basic weather apps, SG Outdoor Guide answers the questions Singaporeans actually ask:

| Question | Feature |
|----------|---------|
| "Can I go jogging?" | 🏃 **Exercise Safety Score** (0-100) combining PSI + UV + temp + humidity |
| "Will my laundry dry?" | 👕 **Laundry Forecast** - YES / NO / SLOW |
| "What should I do today?" | 🎯 **Smart Activity Suggestions** based on current conditions |
| "Is the haze bad?" | 🌬️ **PSI by Region** with health advice |

## 📱 Live Demo

**[sg-outdoor-guide.onrender.com](https://sg-outdoor-guide.onrender.com)**

![Dashboard Preview](https://raw.githubusercontent.com/jonathanwxh-cell/sg-outdoor-guide/main/preview.png)

## ✨ Features

- **🏃 Exercise Score** - GO / CAUTION / AVOID verdict based on real conditions
- **👕 Laundry Forecast** - Because every Singaporean asks this
- **🎯 Activity Suggestions** - Contextual recommendations (rain? → museum. Clear? → ECP cycling)
- **🌡️ Current Conditions** - Temperature, humidity, UV index with visual indicator
- **🌬️ Air Quality** - PSI readings for all 5 regions
- **🌧️ Rain Alerts** - Banner warning when rain expected
- **🌤️ 2-Hour Forecast** - All 47 Singapore areas

## 📊 Data Sources

All data from official **[data.gov.sg](https://data.gov.sg)** APIs:
- NEA 2-hour weather forecast
- NEA 24-hour forecast  
- PSI readings
- UV index
- Air temperature
- Relative humidity

**100% real-time government data. No mockups.**

## 🛠️ Tech Stack

- **Backend:** Python Flask
- **Frontend:** Vanilla HTML/CSS/JS
- **Hosting:** Render (free tier)
- **APIs:** data.gov.sg (free, no key needed)

## 🚀 Deploy Your Own

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/jonathanwxh-cell/sg-outdoor-guide)

Or manually:

```bash
git clone https://github.com/jonathanwxh-cell/sg-outdoor-guide.git
cd sg-outdoor-guide
pip install -r requirements.txt
gunicorn app:app
```

## 🇸🇬 Made for Singapore

Built because existing weather apps don't answer what Singaporeans actually want to know:
- Is it safe to exercise outside?
- Will the afternoon rain ruin my plans?
- Can I hang my laundry?

## 📝 License

MIT - Use it however you want.

---

**[Try it now →](https://sg-outdoor-guide.onrender.com)**
