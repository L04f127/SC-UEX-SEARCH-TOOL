# SC item value page

A search page for Star Citizen item values. Every item in the UEX catalog is listed, with N/A where there is no price. A scheduled job refreshes the data every 6 hours.

## Set up (about 10 minutes, free)

1. Create a new **public** repository on GitHub.
2. Upload everything in this folder, keeping the folder layout: `index.html`, `data.json`, `data/marketplace.csv`, `scripts/update_data.py` and `.github/workflows/update.yml`. If the web uploader skips the hidden `.github` folder, use **Add file > Create new file**, type `.github/workflows/update.yml` as the name and paste the file in.
3. Go to **Settings > Pages**, set the source to **Deploy from a branch**, pick `main` and `/ (root)`, and save. Your page address appears there after a minute.
4. Go to the **Actions** tab, open **Update prices** and click **Run workflow**. The first run takes 5 to 10 minutes because it downloads the whole catalog. It then runs by itself every 6 hours.
5. Optional: if UEX asks for a token or you hit rate limits, create a free token on UEX's My Apps page and add it under **Settings > Secrets and variables > Actions** as `UEX_TOKEN`.

## Notes

- `data.json` starts with the 217-item player-market snapshot so the page works before the first run.
- The player-market averages (sellers ask, buyers offer) come from `data/marketplace.csv`, which does not update by itself. Shop prices and the item list do.
- To change how often it runs, edit the `cron` line in `update.yml`. UEX refreshes most of its data daily, so running more often than every few hours gains little.
- If a run fails, `data.json` stays as it was. Open the failed run in the Actions tab to see why.
