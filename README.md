# Bridge Club Downloader

A cross-platform Python app for downloading bridge results from a club website and exporting them into a standard PBN file that can be imported into BridgePartner and similar offline bridge software.

Features:
- Scrape player or pair result pages from club websites
- Follow historical result links and board lists
- Export boards as Portable Bridge Notation (PBN)
- Works on Linux and Windows with the same Python codebase
- Includes a simple CLI and an optional Tkinter GUI

Repository structure:
- `bridgeclub_downloader/cli.py` — command-line interface
- `bridgeclub_downloader/scraper.py` — HTML scraping and history discovery
- `bridgeclub_downloader/pbn_writer.py` — exports board data to PBN
- `bridgeclub_downloader/gui.py` — optional desktop interface

Quick start:

1. Create and activate a virtual environment
2. Install dependencies
3. Run the CLI with a player or pair page URL

Example:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m bridgeclub_downloader.cli --url "https://undercroft.bridgeaustralia.org/showplayer.asp?id=693016&pair=ns-3" --output results.pbn
```

For Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m bridgeclub_downloader.cli --url "https://undercroft.bridgeaustralia.org/showplayer.asp?id=693016&pair=ns-3" --output results.pbn
```

Notes:
- The app is designed for club sites that expose results in HTML tables and linked board pages.
- Some clubs use JavaScript-heavy layouts; if so, the scraper may need site-specific selectors.
- Historical board pages are discovered by scanning the page for board and date navigation links.

For a full desktop build:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed bridgeclub_downloader/gui.py
```
