# Simple Aniworld Scraper

This is a limited onefile fork of [wolfswolke](https://github.com/wolfswolke)'s Anime/Serien Scraper which I made for simpleness.
This onefile tool will download all Seasons and Episodes of an anime from Aniworld.to.


How to use:

- download or install [ffmpeg](https://ffmpeg.org) (If you download it put it in the same folder as the script)
  
- ARGUMENTS: `aniworld_scraper.py <NAME> <LANGUAGE> <OUTPUT_PATH> <PROVIDER> <DOS_WAITCOUNT> <DOS_ACTIVECOUNT>`
  
### Required:

- name: Enter the anime name you want to download.
- language: Determine the desired language of the files. Common options are: "Deutsch", "Ger-Sub" and "English"

### Optional:

- output_path: Folder path, where the output files should be put. Default is the same folder as the script.
- provider: Provider from where the program downloads the Anime. Available options are "VOE", "Streamtape" or "Vidoza". Default is "VOE" as its the fastest.
- dos_waitcount: How many episodes to download before waiting 60 seconds. Default is 5.
- dos_activecount: Maximum of active downloads. Default is 8.
