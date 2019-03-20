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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# Initialize Coloroma
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

#Adding Suitable Options to our Headless Browser
chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument("--log-level=3")

driver = webdriver.Chrome(executable_path = "chromedriver", chrome_options = chrome_options)


#------  Making soup with BeautifulSoup 4  -------
def make_soup(url):
    soup = None
    try:
        print(f'{Style.DIM}[*] Sending request to {url}...')  
        data = http.request('GET', url).data
        soup = BeautifulSoup(data, 'html.parser')
        print(f'{Fore.GREEN}[*] SUCCESS: Soup for {url[:65]}... is successfully Created')
    except Exception as e:
        print(f'{Fore.RED}[*] FAILED: Unable to access website :(\n[*] Either due to no internet connection or website doesn\'t exist')
        sys.exit()
    return soup

def get_user_chosen_link(link_map):
    index_download = int(
        input(index_string))
    return link_map[index_download]

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
    detDesc = soup.find_all('font',class_='detDesc')[:10]
    for i in range(0, len(detDesc)):
            size = detDesc[i].text.split(',')[1] or None
            size_list.append(size)
    link_dict = {}
    i = 1
    print(f'{Fore.MAGENTA}\n[*]List of available download options:')
    for d in det:
        print(f"[{i}]:{d.text}-{size_list[i-1]}")
        link_dict[i] = d.a.get('href')
        i += 1
    return link_dict

def create_magnet_link(link_dict, search_url): 
    user_link = get_user_chosen_link(link_dict)
    soup = make_soup(search_url.split('/s')
                     [0] + user_link)
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
        elif(type == 'ocean'):
            title = link.a.text
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
    user_link = get_user_chosen_link(ml_links)
    series_link = f'{user_link}/watching.html?ep=0'
    soup = make_soup(series_link)
    ep_list = soup.find(class_ = 'les-content')
    episodes = ep_list.find_all(class_ = 'btn-eps')
    eps_links = link_map_creator(episodes, 'eps', None)
    return eps_links

def create_download_link(eps_links):
    user_link = get_user_chosen_link(eps_links)
    soup = make_soup(user_link)
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

#---------------------------------------------------
#-------- OCEAN OF GAMES And iGet Into PC ----------
#---------------------------------------------------
def get_ocean_link(root_url):
    query_str = '+'.join(args.query.split(' '))
    soup  = make_soup(f'{root_url}?s={query_str}')
    titles = soup.find_all('h2', class_ = 'title')
    og_map = link_map_creator(titles, 'ocean', None)
    user_link = get_user_chosen_link(og_map)
    return user_link

def expand_shadow_element(element):
    shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
    return shadow_root

def get_ocean_download_link(url): 
    driver.get(url)
    driver.find_element_by_xpath("//input[@src ='http://oceanofgames.com/wp-content/uploads/2013/09/button-download.png' and @alt='Download']").click()
    time.sleep(15)
    print('Going to Downloads')
    driver.get('chrome://downloads/')
    if(driver.window_handles):
        driver.switch_to_window(driver.window_handles[0])
    root1 = driver.find_element_by_tag_name('downloads-manager')
    shadow_root1 = expand_shadow_element(root1)
    print(shadow_root1)
    root2 = shadow_root1.find_element_by_css_selector('downloads-item')
    shadow_root2 = expand_shadow_element(root2)

    url = shadow_root2.find_element_by_id("url")
    link = url.get_attribute("href")
    driver.quit()
    return link

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

    elif (args.method == 'og' or args.method == 'ocean'):
        root_url = 'http://oceanofgames.com/'
        url = get_ocean_link(root_url)
        download_link = get_ocean_download_link(url)
    pyperclip.copy(download_link)
    # Open Free Download Manager
    Application(backend="uia").start(
        cmd_line=r"C:/Program Files/FreeDownloadManager.ORG/Free Download Manager/fdm.exe")

    download_with_fdm(download_link)

if (__name__ == '__main__'):
    main()


    
    


   
