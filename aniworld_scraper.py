
def download_voe(hls_url, file_name, anime_name_full, episodes_all):
    try:
        ffmpeg_cmd = ['ffmpeg', '-i', hls_url, '-c', 'copy', file_name]
        run(ffmpeg_cmd, check=True, stdout=PIPE, stderr=PIPE)
        now = datetime.now()
        current_time = now.strftime("%d/%m/%Y %H:%M")
        print(f"[{current_time} | INFO] VOE -> Finished download of {anime_name_full}.\n")
    except CalledProcessError as e:
        print(e)
        if exists(file_name):
            remove(file_name)
            now = datetime.now()
            current_time = now.strftime("%d/%m/%Y %H:%M")
            print(f"[{current_time} | ERROR] VOE -> Server Error. Can't download {file_name}.\n")


def download_other(link, file_name, anime_provider, anime_name_full, episodes_all):
    try:
        r = get(link, stream=True)
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        if getsize(file_name) != 0:
            now = datetime.now()
            current_time = now.strftime("%d/%m/%Y %H:%M")
            print(f"[{current_time} | INFO] {anime_provider} -> Finished download of {anime_name_full}.\n")
        else:
            if exists(file_name):
                remove(file_name)
                now = datetime.now()
                current_time = now.strftime("%d/%m/%Y %H:%M")
                print(f"[{current_time} | ERROR] {anime_provider} -> Server Error. Can't download {file_name}.\n")
    except Exception as e:
        print(e)
        if exists(file_name):
            remove(file_name)
            now = datetime.now()
            current_time = now.strftime("%d/%m/%Y %H:%M")
            print(f"[{current_time} | ERROR] {anime_provider} -> Server Error. Can't download {file_name}.\n")


def fetch_cache_url(url, provider, failed):
    STREAMTAPE_PATTERN = compile(r'get_video\?id=[^&\'\s]+&expires=[^&\'\s]+&ip=[^&\'\s]+&token=[^&\'\s]+\'')
    html_page = urlopen(url)
    try:
        if provider == "Vidoza":
            soup = BeautifulSoup(html_page, features="html.parser")
            cache_link = soup.find("source").get("src")
        elif provider == "VOE":
            content = html_page.read().decode('utf-8').replace("\n", "").split()
            for line in content:
                if "http" in line and ".m3u8" in line:
                    if line.startswith('"'):
                        line = line[1:]
                    if line.endswith('"'):
                        line = line[:-1]
                    if line.endswith('");'):
                        line = line[:-3]

                    cache_link = line

        elif provider == "Streamtape":
            cache_link = STREAMTAPE_PATTERN.search(html_page.read().decode('utf-8'))
            if cache_link is None:
                if failed:
                    return None
                return fetch_cache_url(url, provider, True)
            cache_link = "https://" + provider + ".com/" + cache_link.group()[:-1]
    except AttributeError:
        if not failed:
            return fetch_cache_url(url, provider, True)
        else:
            return None

    return cache_link


def fetch_redirect_url(aniworld_season_and_episode_url, anime_language, anime_provider):
    aniworld_season_and_episode_url_html = get(aniworld_season_and_episode_url)

    soup = BeautifulSoup(aniworld_season_and_episode_url_html.content, "html.parser")
    lang_key_mapping = {}
    # Find the div with class "changeLanguageBox"
    change_language_div = soup.find("div", class_="changeLanguageBox")
    if change_language_div:
        # Find all img tags inside the div to extract language and data-lang-key
        lang_elements = change_language_div.find_all("img")
        for lang_element in lang_elements:
            language = lang_element.get("alt", "") + "," + lang_element.get("title", "")
            data_lang_key = lang_element.get("data-lang-key", "")
            if language and data_lang_key:
                lang_key_mapping[language] = data_lang_key
    new_dict = {}
    already_seen = set()
    for key, value in lang_key_mapping.items():
        new_dict[value] = set([element.strip() for element in key.split(',')])
    return_dict = {}
    for key, values in new_dict.items():
        for value in values:
            if value in already_seen and value in return_dict:
                del return_dict[value]
                continue
            if value not in already_seen and value not in return_dict:
                return_dict[value] = key
                already_seen.add(value)
    lang_key_mapping = return_dict
    lang_key = lang_key_mapping.get(anime_language)
    if not lang_key:
        return False, lang_key_mapping
    matching_li_elements = soup.find_all("li", {"data-lang-key": lang_key})
    matching_li_element = next((li_element for li_element in matching_li_elements if li_element.find("h4").get_text() == anime_provider), None)

    try:
        if matching_li_element:
                href_value = matching_li_element.get("data-link-target", "")

        link_to_redirect = f"https://aniworld.to{href_value}"
        return True, link_to_redirect
    except:
        return False, f"{anime_provider} does not provide this episode."

def fetch_episodecount(aniworld_url, aniworld_season):
    aniworld_season_url = aniworld_url + f"/staffel-{aniworld_season}"
    episode_count = 1
    aniworld_season_url_html = get(aniworld_season_url)
    soup = BeautifulSoup(aniworld_season_url_html.content, features="html.parser")
    for link in soup.findAll('a'):
        episode = str(link.get("href"))
        if "/staffel-{}/episode-{}".format(aniworld_season, episode_count) in episode:
            episode_count = episode_count + 1
    return episode_count - 1

def fetch_seasoncount(aniworld_url):
    aniworld_seasoncount = 1
    aniworld_url_html = get(aniworld_url)
    soup = BeautifulSoup(aniworld_url_html.content, features="html.parser")
    for link in soup.findAll('a'):
        seasons = str(link.get("href"))
        if "/staffel-{}".format(aniworld_seasoncount) in seasons:
            aniworld_seasoncount += 1
    return aniworld_seasoncount - 1

def download_aniworld(anime_name, anime_language, output_path, anime_provider, dos_waitcount, dos_activecount):
    anime_name = anime_name.lower().replace(" ", "-")
    aniworld_url = f"https://aniworld.to/anime/stream/{anime_name}"
    if anime_language.lower() == "deutsch":
        anime_language = "Deutsch"
    aniworld_response = get(aniworld_url)

    if aniworld_response.status_code != 200:
        print(f"Web response was not 200. Status Code: {aniworld_response.status_code}")
        return False

    aniworld_seasons = fetch_seasoncount(aniworld_url=aniworld_url)

    if aniworld_seasons == 0:
        print(f"There is no anime called {anime_name}. Anime has 0 seasons")
        return False

    aniworld_seasons_and_episodes = []
    aniworld_total_episodes = 0

    for aniworld_season in range(aniworld_seasons):
        aniworld_season += 1
        aniworld_season_episodes = fetch_episodecount(aniworld_url=aniworld_url, aniworld_season=aniworld_season)
        aniworld_seasons_and_episodes.append(f"{aniworld_season}_{aniworld_season_episodes}")
        aniworld_total_episodes += aniworld_season_episodes

    dos_count = 0

    language_failed = 0
    for aniworld_season_and_episode in aniworld_seasons_and_episodes:
        aniworld_season = int(aniworld_season_and_episode.split("_")[0])
        aniworld_episodes = int(aniworld_season_and_episode.split("_")[1])

        for aniworld_episode in range(aniworld_episodes):
            aniworld_episode += 1

            anime_name_full = f"{anime_name} - s{aniworld_season:02}e{aniworld_episode:02} - {anime_language}.mp4"
            output_filename = f"{output_path}{anime_name} - s{aniworld_season:02}e{aniworld_episode:02} - {anime_language}.mp4"

            if exists(output_filename):
                print(f"ALREADY EXISTS {output_filename}")
                continue
            else:
                dos_count += 1
                if dos_count > dos_waitcount:
                    sleep(60)
                    dos_count = 1
            aniworld_season_and_episode_url = f"{aniworld_url}/staffel-{aniworld_season}/episode-{aniworld_episode}"
            redirect_status, redirect_url = fetch_redirect_url(aniworld_season_and_episode_url=aniworld_season_and_episode_url, anime_language=anime_language, anime_provider=anime_provider)

            if redirect_status:
                cache_url = fetch_cache_url(url=redirect_url, provider=anime_provider, failed=False)
                if cache_url is None:
                    now = datetime.now()
                    current_time = now.strftime("%d/%m/%Y %H:%M")
                    print(f"[{current_time} | ERROR] {anime_provider} -> Can't find cache URL for {anime_name_full}.\n")
                    continue

                now = datetime.now()
                current_time = now.strftime("%d/%m/%Y %H:%M")
                print(f"[{current_time} | INFO] {anime_provider} -> Starting download of {anime_name_full}.\n")

                if anime_provider == "VOE":
                    Thread(target=download_voe, args=(cache_url, output_filename, anime_name_full, aniworld_total_episodes)).start()
                else:
                    while active_count() > dos_activecount:
                        sleep(5)
                    Thread(target=download_other, args=(cache_url, output_filename, anime_provider, anime_name_full, aniworld_total_episodes)).start()
            else:
                if " does not provide this episode." in redirect_url:
                    now = datetime.now()
                    current_time = now.strftime("%d/%m/%Y %H:%M")
                    print(f"[{current_time} | ERROR] {anime_provider} -> {anime_name_full} not provided.\n")
                elif anime_provider == "VOE":
                    language_failed += 1
                    now = datetime.now()
                    current_time = now.strftime("%d/%m/%Y %H:%M")
                    print(f"[{current_time} | ERROR] {anime_provider} -> Language '{anime_language}' for {anime_name_full} is invalid. Languages: {list(redirect_url.keys())}.\n")
                    if language_failed == aniworld_total_episodes:
                        print(f"Anime does not support {anime_language} for language.")
                        return False

    while True:
        threads_string = ""
        for thread in enumerate():
            threads_string += thread.name
        if not "download_voe" in threads_string and not "download_other" in threads_string:
            break
        now = datetime.now()
        current_time = now.strftime("%d/%m/%Y %H:%M")
        print(f'[{current_time} | INFO] {anime_provider} -> {threads_string.count("download_voe") + threads_string.count("download_other")} download(s) still running...\n')
        sleep(30)


    if anime_provider == "VOE":
        download_aniworld(anime_name=anime_name, anime_language=anime_language, output_path=output_path, anime_provider="Streamtape", dos_waitcount=dos_waitcount, dos_activecount=dos_activecount)
    elif anime_provider == "Streamtape":
        download_aniworld(anime_name=anime_name, anime_language=anime_language, output_path=output_path, anime_provider="Vidoza", dos_waitcount=dos_waitcount, dos_activecount=dos_activecount)

    file_count = 0
    for file in listdir(output_path):
        if file.startswith(anime_name):
            file_count += 1

    print(f"Finished download of {anime_name}. Available Episodes {file_count}/{aniworld_total_episodes}")
    return True

if __name__ == '__main__':
    from bs4 import BeautifulSoup
    from requests import get
    from os.path import exists, getsize
    from os import remove, listdir
    from time import sleep
    from re import compile
    from urllib.request import urlopen
    from subprocess import run, PIPE, CalledProcessError
    from threading import Thread, active_count, enumerate
    from datetime import datetime
    from sys import argv, exit

    if len(argv) < 3:
        now = datetime.now()
        current_time = now.strftime("%d/%m/%Y %H:%M")
        print(f"[{current_time} | ERROR] Not enough arguments. -> python aniworld_scraper.py <anime_name> <language>")
        exit()

    anime_name = argv[1]
    anime_language = argv[2]
    try:
        output_path = argv[3] + "\\"
    except:
        output_path = ""
    try:
        anime_provider = argv[4]
    except:
        anime_provider = "VOE"
    try:
        dos_waitcount = argv[5]
    except:
        dos_waitcount = 5
    try:
        dos_activecount = argv[6]
    except:
        dos_activecount = 8

    download_aniworld(anime_name=anime_name, anime_language=anime_language, output_path=output_path, anime_provider=anime_provider, dos_waitcount=dos_waitcount, dos_activecount=dos_activecount)
