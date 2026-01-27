<h1 style="display: flex; align-items: center; gap: 12px;">
  <img src="images/icon.png" width="35" alt="Neverin logo" style="align-self: flex-end;">
  <span>Neverin – Home Assistant Integration</span>
</h1>


An unofficial Home Assistant integration for Neverin, providing access to weather station data from over 1,000 stations across Croatia and the region.

The integration uses [**Neverin weather data**](https://neverin.hr) and allows easy station selection directly from the Home Assistant UI.

---

## ✨ Features

- 📡 Fetches available Neverin weather stations
- ⚙️ Easy UI-based setup (Config Flow)
- 🏠 Native Home Assistant integration

---

## 📦 Installation (HACS)

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=potrgani&repository=neverin&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." /></a>

or

### 1️⃣ Add Custom Repository to HACS

1. Open **HACS**
2. Go to **Integrations**
3. Click **⋮ (top right)** → **Custom repositories**
4. Add:
   - **Repository**:
     ```
     https://github.com/potrgani/neverin
     ```
   - **Category**: `Integration`
5. Click **Add**

---

### 2️⃣ Install the Integration

1. In **HACS → Integrations**
2. Search for **Neverin**
3. Click **Download**
4. Restart Home Assistant

---

## ⚙️ Configuration

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **Neverin**
4. Select your desired **Neverin station** from the list
5. Save the configuration

🎉 The integration is now ready to use!

---

## 🧠 Notes

- Only **active stations** are shown
- Data availability depends on the Neverin API

---

## 🐞 Issues & Contributions

If you encounter a bug or have a suggestion:
- Open a **GitHub Issue** at  
  https://github.com/potrgani/neverin/issues
- Or submit a **Pull Request**

Contributions are welcome 👍

---

## ⚠️ Disclaimer

This integration is **not an official Neverin product**.  
It is a community-developed project.


