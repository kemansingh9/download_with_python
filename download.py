from pywinauto.application import Application
from bs4 import BeautifulSoup
import urllib3
import random
import argparse
import pyautogui
from user_agents import user_agent_list
from imagesearch import *
import time 
import sys
import pyperclip
from colorama import init, Fore, Back, Style
init(autoreset = True)

# Command Line Interface
argument_parser = argparse.ArgumentParser(
    description='Download torrent from piratesbay through terminal')
argument_parser.add_argument(
    'query', metavar='query', type=str, help='Search Term for Torrents')
argument_parser.add_argument('--method', metavar='method', default='torrent', type=str, help='Method of downloading data')

args = argument_parser.parse_args()

# Creating a random User Agent
user_agent = {'user-agent': random.choice(user_agent_list)}
# Disable Http request warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# create the http protocol
http = urllib3.PoolManager(10, headers=user_agent)

index_string = '[*] Enter the index of File which you want to download: '

#------  Making soup with BeautifulSoup 4  -------
def make_soup(url):
    soup = None
    try:
        print(f'{Style.DIM}[*] Sending request to {url[:65]}...')  
        data = http.request('GET', url).data
        soup = BeautifulSoup(data, 'html.parser')
        print(f'{Fore.GREEN}[*] SUCCESS: Soup for {url[:65]}... is successfully Created')
    except Exception as e:
        print(f'{Fore.RED}[*] FAILED: Unable to access website :(\n[*] Either due to no internet connection or website doesn\'t exist')
        sys.exit()
    return soup

#-----------------------------
# Download from ThePiratesBay
#-----------------------------
def create_search_url(soup):
    print('\n[*] Creating Search Url....')
    url = soup.find(class_='domain').text
    search_term = '+'.join(args.query.split(' '))
    search_url = url + '/s/?q=' + search_term
    return search_url


def create_link_map(search_url, soup):
    print('\n[*] Creating Link Map....')
    det = soup.find_all(class_='detName')[:10]
    size_list = []
    detDesc = soup.find_all(class_='detDesc')[:20]
    for i in range(0, len(detDesc), 2):
        size_list.append(detDesc[i].text.split(',')[1])
    link_dict = {}
    i = 1
    print(f'{Fore.MAGENTA}\n[*]List of available download options:')
    for d in det:
        print(f"[{i}]:{d.text}-{size_list[i-1]}")
        link_dict[i] = d.a.get('href')
        i += 1
    return link_dict

def create_magnet_link(link_dict, search_url): 
    index_download = int(
        input(index_string))

    soup = make_soup(search_url.split('/s')
                     [0] + link_dict[index_download])
    return soup.find(class_='download').a.get('href')

#--------------------------------
# Controlling FDM with pyautogui
#--------------------------------
def drag_mouse_to_image(image, x_inc, y_inc): 
    pos = imagesearch_loop(image, 0.5)
    pyautogui.moveTo(pos[0] + x_inc, pos[1]+y_inc)
    pyautogui.click()

def download_with_fdm(link):
    drag_mouse_to_image("add_fdm.png", 0, 0)
    drag_mouse_to_image("download_form.png", 50, 90)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.typewrite(link)
    drag_mouse_to_image("ok.png", 0, 0)
    drag_mouse_to_image("download.png", 0, 0)


#-------------------------------------------
# Download from SeriesOnline
#-------------------------------------------

def first_page_results(query):
    search_url = f'https://www.google.com/search?q={query}'
    soup = make_soup(search_url)
    rows = soup.find_all(class_ = 'r')
    return rows

def get_links(query):
    rows = first_page_results(query)
    links = []
    for row in rows:
        links.append(row.a.get('href'))
    return links

def get_working_url():
    query = 'series+online'
    links = get_links(query)
    for link in links:
        if 'seriesonline' in link:
            soup = make_soup(link) 
            if(len(str(soup).split(' ')) > 100):
                break
            elif (len(str(soup).split(' ')) < 100) and (links[-1] != link):
                print(f'{Fore.BLUE}[*] {link} didn\'t work\n[*] Trying next link....')
            else:
                print(f'{Fore.RED}[*] FAILED: All links on google first page aren\'t working')
                link = None
        else:
            print(f'[*] Ignoring non-useful link: {link}')

    return link

#----------- Utility Function ------------
def link_map_creator(links, type, root_link):
    link_map = {}
    i = 1
    print(f'{Fore.MAGENTA}[*] Choose one of the following options:')
    for link in links:
        if (type == 'eps'):
            title = link['title']
            url_tail = link["player-data"].replace('streaming.php', 'download')
            url = f'https:{url_tail}'
        elif (type == 'search'):
            title = link.h2.text
            url = root_link+link.a.get('href')
        elif(type == 'download'):
            title = link.text.strip()
            url = link.a.get('href')
        print(f'{[i]}- {title}')
        link_map[i] = url
        i+=1
    
    return link_map

def fmov_link_map(search_link, link):
    search_link = '-'.join(search_link.split(' '))
    soup = make_soup(search_link)
    ml_items = soup.find_all(class_ = 'ml-item')
    ml_links = link_map_creator(ml_items, 'search', link)
    return ml_links
    

def eps_link_map(ml_links):
    index_option = int(input(index_string))
    series_link = f'{ml_links[index_option]}/watching.html?ep=0'
    soup = make_soup(series_link)
    ep_list = soup.find(class_ = 'les-content')
    episodes = ep_list.find_all(class_ = 'btn-eps')
    eps_links = link_map_creator(episodes, 'eps', None)
    return eps_links

def create_download_link(eps_links):
    download_option = int(input(f'{index_string}'))
    download_page = eps_links[download_option]
    soup = make_soup(download_page)
    download_links = soup.find_all(class_ = 'dowload')
    print(f'{Fore.MAGENTA}[*] Choose one of the following options:')
    d_link_map = link_map_creator(download_links, 'download', None)
    index_option = int(input(index_string))
    if (index_option in d_link_map.keys()):
        download_link = d_link_map[index_option]
    else:
        print('[*] Bad option. Please choose the options from above')
        create_download_link(eps_links)
    return download_link

#--------------------- MAIN FUNCTION ----------------------
def main():
    if(args.method =='torrent' or args.method == 'tor'):
        url = 'https://piratebay-proxylist.se/'
        pirate_proxy_soup = make_soup(url)
        search_url = create_search_url(pirate_proxy_soup)
        pirate_bay_soup = make_soup(search_url)
        link_dict = create_link_map(search_url, pirate_bay_soup)
        download_link = create_magnet_link(link_dict, search_url)
    
    elif(args.method == 'fmov' or args.method == 'seriesonline'):
        search_str = args.query
        link = get_working_url()
        search_link = f'{link}movie/search/{search_str}'
        ml_links = fmov_link_map(search_link, link)
        eps_links = eps_link_map(ml_links)
        download_link = create_download_link(eps_links)
    
    pyperclip.copy(download_link)
    # Open Free Download Manager
    Application(backend="uia").start(
        cmd_line=r"C:/Program Files/FreeDownloadManager.ORG/Free Download Manager/fdm.exe")

    download_with_fdm(download_link)

if (__name__ == '__main__'):
    main()
    