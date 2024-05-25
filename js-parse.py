#!/usr/bin/env python3
import re, os, requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import jsbeautifier
import argparse
import httpx

pretty_files = []
get_py_filename = os.path.basename(__file__)
target= ""
all_dirs=[]
intro_logo = f"""\u001b[31m

░░░░░██╗░██████╗░░░░░░██████╗░░█████╗░██████╗░░██████╗███████╗
░░░░░██║██╔════╝░░░░░░██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝
░░░░░██║╚█████╗░█████╗██████╔╝███████║██████╔╝╚█████╗░█████╗░░
██╗░░██║░╚═══██╗╚════╝██╔═══╝░██╔══██║██╔══██╗░╚═══██╗██╔══╝░░
╚█████╔╝██████╔╝░░░░░░██║░░░░░██║░░██║██║░░██║██████╔╝███████╗
░╚════╝░╚═════╝░░░░░░░╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░╚══════╝
      




--------------------------------------------------------------\u001b[0m"""
class NewlineFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

parser = argparse.ArgumentParser(prog= f"python {get_py_filename}", description='\u001b[96mdescription: parses urls from js files', epilog=
f'''
\u001b[91mbasic usage:\u001b[0m python {get_py_filename } https://youtube.com
\u001b[91msingle file:\u001b[0m python {get_py_filename } https://youtube.com -m
\u001b[91mmulti-file:\u001b[0m python {get_py_filename } https://youtube.com -i
\u001b[91mstdout:\u001b[0m python {get_py_filename } https://youtube.com -S   
''', formatter_class=NewlineFormatter, usage=f'{intro_logo}\n\u001b[32m%(prog)s [options] url\u001b[0m')

parser.add_argument("url", help="\u001b[96mspecify url with the scheme of http or https")
parser.add_argument("-s", "--save", help="save prettified js files", action="store_true")
parser.add_argument("-b", "--blacklist", help="blacklist subdomains/domains", nargs="+", default="")
parser.add_argument("-S", "--stdout", help="stdout friendly, displays urls only in stdout", action="store_true")
parser.add_argument("-f", "--filter", help="removes false positives with httpx/requests (use at your own risk)", action="store_true")
parser.add_argument("-k", "--kontrol", help="removes false positives with httpx/requests (use at your own risk)", choices=['ALL', 'API', 'FORBIDDEN'])

group = parser.add_mutually_exclusive_group()
group.add_argument("-m", "--merge", help="create file and merge all urls into it", action="store_true")
group.add_argument("-i", "--isolate", help="create multiple files and store urls where they were parsed from", action="store_true")
args = parser.parse_args()
target_url = args.url

if (target_url[len(target_url) - 1] == '/'):
    target_url = args.url[:len(target_url)-1]

intro_logo = f"""\u001b[31m


░░░░░██╗░██████╗░░░░░░██████╗░░█████╗░██████╗░░██████╗███████╗
░░░░░██║██╔════╝░░░░░░██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝
░░░░░██║╚█████╗░█████╗██████╔╝███████║██████╔╝╚█████╗░█████╗░░
██╗░░██║░╚═══██╗╚════╝██╔═══╝░██╔══██║██╔══██╗░╚═══██╗██╔══╝░░
╚█████╔╝██████╔╝░░░░░░██║░░░░░██║░░██║██║░░██║██████╔╝███████╗
░╚════╝░╚═════╝░░░░░░░╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░╚══════╝
      


{('parsing webpage: ' + target_url)}

--------------------------------------------------------------\u001b[0m"""

def verify_files():
    if (args.merge or args.isolate):
        process_files_with_tqdm()
        if (args.merge):
            write_files()
        print(f'parsed: {len(all_dirs)} urls')
    elif(args.stdout):
        process_files_without_tqdm()
        stdout_dirs()
    else:
        process_files_with_tqdm()
        stdout_dirs()
        print(f'\n\n\n***parsed: {len(all_dirs)} urls***')
    if(args.save):
        move_stored_files()
        print('saved js files')
        print('done')
    
def extract_files(url):
    for tags in fetch_html(url):
        try: 
            js_file = tags['src']
            yield js_file
        except KeyError:
            pass

def fetch_html(url):
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'}
    req=""

    try:
        req = requests.get(url, headers=headers)
        soup = BeautifulSoup(req.content, "html.parser")
        list_tags = soup.find_all('script')
    except ( requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema, requests.exceptions.InvalidURL):
            print(f'NOT FOUND: invalid url, missing, or does not start with http/https protocol in {url}')
            quit()

    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.content, "html.parser")
    list_tags = soup.find_all('script')
    return list_tags

def store_urls(url):
    try:
        global target
        target, file_name = re.search("(?:[a-zA-Z0-9-](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9-])?\.)+[a-zA-Z]{2,}", url).group(0), re.search("([^/]*\.js)", url).group(0)
        parsed_js_directory_path = f"{target}/parsed-urls/"
        parsed_files_directory_path = f"{target}/parsed-files/"

        if (args.isolate or args.merge):
            try:
                os.makedirs(parsed_js_directory_path)
            except FileExistsError:
                pass
            if(args.save):
                os.mkdir(parsed_files_directory_path)

    except FileExistsError:
        pass
    except AttributeError:
        pass
   
    for quoted_dir in extract_urls(url):
        try:
            if (args.isolate):
                dir = quoted_dir.strip('"')
                with open(f"{target}/parsed-urls/{file_name}+dirs.txt", "a", encoding="utf-8") as directories:
                    directories.write(dir + '\n')
            elif (args.merge):
                dir = quoted_dir.strip('"')
                all_dirs.append(dir)
            else:
                dir = quoted_dir.strip('"')
                all_dirs.append(dir)
        finally:
             if(args.save):
                parsed_files_directory_path = f"{target}/parsed-files/"
                if not (os.path.exists(parsed_files_directory_path)):
                    os.makedirs(parsed_files_directory_path)

def extract_urls(url):
    req = fetch_js(url)
    absolute_pattern = r'(["\'])(https?://(?:www\.)?\S+?)\1'
    relative_dirs = re.findall('["\'][\w\.\?\-\_]*/[\w/\_\-\s\?\.=]*["\']*', req)
    absolute_urls = re.findall(absolute_pattern, req)
    absolute_urls = [url[1] for url in absolute_urls] 
    all_dirs = relative_dirs + absolute_urls
    return all_dirs

def fetch_js(url):
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'}
    req = requests.get(url, headers=headers).text
    req = jsbeautifier.beautify(req)
    if(args.save):
        pretty_files.append(url)
        with open(f"pretty-file{len(pretty_files)}.txt", 'w', encoding="utf-8") as prettyJsFile:
            prettyJsFile.write(url + '\n') 
            prettyJsFile.write(req) 
    return req

def move_stored_files():
    for prettyfile in range(1, len(pretty_files) + 1):
        source_path = os.getcwd()
        source_filename = f"pretty-file{prettyfile}.txt"
        source_file = os.path.join(source_path, source_filename)
        destination_dir = os.path.join(source_path, f"{target}/parsed-files")
        destination_file = os.path.join(destination_dir, source_filename)
        os.replace(source_file, destination_file)

def write_files():
    remove_dupes()
    if (args.filter):
        filter_urls_with_tqdm()
    with open(f"{target}/parsed-urls/all_urls.txt", "w", encoding="utf-8") as directories:
        directories.write('')
    with open(f"{target}/parsed-urls/all_urls.txt", "a", encoding="utf-8") as directories:
        for unique_dir in all_dirs:
            directories.write(clean_urls(unique_dir) + '\n')

def stdout_dirs():
    remove_dupes()
    if (args.filter and args.stdout):
        filter_urls_without_tqdm()
    else:
        filter_urls_with_tqdm()
    for dir in all_dirs:
        print(clean_urls(dir))
        

def remove_dupes():
    all_dirs[:] = list(dict.fromkeys(all_dirs))

def process_files_with_tqdm():
    blacklist = args.blacklist
    custom_bar_format = "\033[32m{desc}\033[0m: [{n}/{total} {percentage:.0f}%] \033[31mCurrent:\033[0m [{elapsed}] \033[31mRemaining:\033[0m [{remaining}] "
    total_items = len(list(extract_files(target_url)))
    for js_file in tqdm(extract_files(target_url), desc="Extracted", unit='URL', bar_format=custom_bar_format, total=total_items, position=0, dynamic_ncols=True, leave=True):
        if any(domain in js_file for domain in blacklist):
            pass
        else:
                if 'http' in js_file or 'https' in js_file:
                    if target_url in js_file:
                        print(js_file, flush=True)
                        store_urls(js_file)
                else:
                    print(js_file, flush=True)
                    store_urls(target_url + js_file)

def process_files_without_tqdm():
    blacklist = args.blacklist
    for js_file in extract_files(target_url):
        if any(domain in js_file for domain in blacklist):
            pass
        else:
                if 'http' in js_file or 'https' in js_file:
                    if target_url in js_file:
                        store_urls(js_file)
                else:
                    store_urls(target_url + js_file)

def filter_urls_without_tqdm():
    for dir in all_dirs[:]:
        try:
            if (dir[:4] == "http"):
                get_status, post_status = httpx.get(dir, follow_redirects=True).status_code, httpx.post(dir, follow_redirects=True).status_code
              
            elif (dir[0] != "/"):
                get_status, post_status = httpx.get(args.url + f'/{dir}', follow_redirects=True).status_code, httpx.post(args.url + f'/{dir}', follow_redirects=True).status_code
                    
            else:
                get_status, post_status = httpx.get(args.url + dir, follow_redirects=True).status_code, httpx.post(args.url + dir, follow_redirects=True).status_code
            
            if (get_status == 404 and post_status == 404):
                all_dirs.remove(dir)
            elif (post_status != 405 and post_status != 404):
                pass
            elif (get_status != 404):
                pass
            else:
                all_dirs.remove(dir)
                
        except:
            all_dirs.remove(dir)

def filter_urls_with_tqdm():
    print('\nVerifying URLS, please wait')
    custom_bar_format = "\033[32m{desc}\033[0m: [{n}/{total} {percentage:.0f}%] \033[31mTime-Taking:\033[0m [{elapsed}] \033[31mTime-Remaining:\033[0m [{remaining}] "
    total_items = len(all_dirs)
    for dir in tqdm(all_dirs[:], desc="Verifying", unit='URL', total=total_items, bar_format=custom_bar_format, position=0, dynamic_ncols=True, leave=True):
        try:
            if (dir[:4] == "http"):
                get_status, post_status = httpx.get(dir, follow_redirects=True).status_code, httpx.post(dir, follow_redirects=True).status_code
              
            elif (dir[0] != "/"):
                get_status, post_status = httpx.get(args.url + f'/{dir}', follow_redirects=True).status_code, httpx.post(args.url + f'/{dir}', follow_redirects=True).status_code
                    
            else:
                get_status, post_status = httpx.get(args.url + dir, follow_redirects=True).status_code, httpx.post(args.url + dir, follow_redirects=True).status_code
            
            if (get_status == 404 and post_status == 404):
                all_dirs.remove(dir)
                print(dir + " " * 2 + f"{ [get_status]}  [GET]", flush=True)
            elif (get_status != 404 and post_status != 404 and post_status != 405):
                print(dir + " " * 2 + f"{ [get_status]} {[post_status]}  [GET] [POST]", flush=True)
            elif (post_status != 405 and post_status != 404):
                print(dir + " " * 2 + f"{ [post_status]}  [POST]", flush=True)
            elif (get_status != 404):
                print(dir + " " * 2 + f"{ [get_status]}  [GET]", flush=True)
            else:
                print(dir + " " * 2 + f"{ [get_status]}  [GET]", flush=True)
                all_dirs.remove(dir)
                
        except:
            all_dirs.remove(dir)
        
def clean_urls(url):
    if(url[:4] == "http"):
        return url
    elif (url[0] != "/"):
        url = "/" + url
        return url
    else:
        return url

if __name__ == "__main__":
    if (args.stdout):
        pass
    else:
        print(intro_logo)
    verify_files()
    pass

