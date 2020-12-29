from signal import signal, SIGINT
from bs4 import BeautifulSoup
from sys import exit
from git import Repo
import urllib.parse
import subprocess
import requests
import tempfile
import datetime
import base64
import shutil
import time
import os

'''
 _     _       _    _   _       _
| |   (_)     | |  | | | |     | |
| |    _ _ __ | | _| |_| |_   _| |__
| |   | | '_ \| |/ /  _  | | | | '_ \
| |___| | | | |   <| | | | |_| | |_) |
\_____/_|_| |_|_|\_\_| |_/\__,_|_.__/

How to get the HTML file
LinkedIn -> Companies page -> People -> Scroll all the way to the bottom
-> Inspect element -> Inspector -> Right Click on the top HTML tag
-> go to copy and select "Outer HTML"

'''

GITHUB_USERNAME = b"username"  # CHANGE ME
GITHUB_PASSWORD = b"api key"  # CHANGE ME
TRUFFLE_HOG_PATH = "/path/to/truffleHog/truffleHog.py" # CHANGE ME
SHHGIT_PATH = "/path/to/shhgit" # CHANGE ME
FILE_NAME = "linkedin_html_file.html" # CHANGE ME
COMPANY_NAME = "company name"  # CHANGE ME
COMPANY_NAME2 = "subsidiary"  # CHANGE ME

# Usage: python3 linkhub.py

################ NO NEED TO CHANGE ANYTHING BELOW ################

TOKEN = base64.b64encode(GITHUB_USERNAME + b":" + GITHUB_PASSWORD).decode('ascii')


def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nCTRL-C detected. Exiting gracefully')
    exit(0)


# Tells python to stop the program if CTRL + C is hit
signal(SIGINT, handler)


def runcommand(cmd):
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            universal_newlines=True)
    std_out, std_err = proc.communicate()
    return proc.returncode, std_out, std_err


def get_repos(valid_accounts: list) -> dict:
    """
    Goes through each account and finds all repos which are not forked, adding
    them to a dictionary.
    :param valid_accounts: A list of valid github usernames
    :return: A dictionary where the key is the username and value is a list of repos
    """
    githubrepos = {}  # A dict of all the github repos with the username being the key
    # Goes through each confirmed github. Grabs all the repos and adds it to the dict
    for act in valid_accounts:
        print('Getting {} repo info'.format(act))
        while True:
            try:
                rl = requests.get('https://api.github.com/rate_limit', headers={"Authorization": "Basic {}".format(TOKEN)})
                break
            except Exception as e:
                print('Getting rate limit info failed. Sleeping for 3 seconds.'.format(act))
                time.sleep(3)

        requests_left = rl.json()['resources']['search']['remaining']
        unlock_epoch = rl.json()['resources']['search']['reset']
        if requests_left == 0:
            sleep = (int(unlock_epoch) - int(datetime.datetime.now().timestamp())) + 3
            time.sleep(sleep)
        while True:
            try:
                r = requests.get('https://api.github.com/users/{}/repos'.format(act), headers={"Authorization": "Basic {}".format(TOKEN)})
                break
            except Exception as e:
                print('Listing {} repos failed. Sleeping for 3 seconds.'.format(act))
                time.sleep(3)
        json = r.json()
        if json != []:
            for num in range(len(json)):
                if json[num]['fork'] == False:
                    name = json[num]['name']
                    if act in githubrepos:
                        githubrepos[act].append(name)
                    else:
                        githubrepos[act] = [name]
    return githubrepos


def clone_git_repo(github_URL: str) -> str:
    """
    Creates a location for the URL to be cloned and clones it, then returns the path
    :param github_URL: The github repo URL
    :return: The local path to the repo
    """
    #  Make a path to a random dir in /tmp to use
    project_path = tempfile.mkdtemp()
    fails = 0
    while fails < 3:
        try:
            Repo.clone_from(github_URL, project_path)
            break
        except Exception:
            fails += 1  # Fails is only used because in some instances github repos are issued DMCA take downs and can not be cloned
            print('\nERROR: {} could not be cloned!\n'.format(github_URL))
            time.sleep(1)
    if fails == 3:
        return None
    return project_path


def find_secrets(account_repos: dict):
    """
    Goes through each repo for each account, clones it locally and uses multiple
    repo search tools to try and find secrets.
    :param account_repos: A dictionary where the key is the username and value is a list of repos
    """
    out_shhgit = "shhgit.{}.{}.txt".format(str(int(datetime.datetime.now().timestamp())), FILE_NAME)
    out_trufflehog = "trufflehog.{}.{}.txt".format(str(int(datetime.datetime.now().timestamp())), FILE_NAME)
    with open(out_shhgit, 'a') as fp:
        fp.write("\n\nHIGH PROBABILITY DETECTIONS\n")
    with open(out_trufflehog, 'a') as fp:
        fp.write("\n\nHIGH PROBABILITY DETECTIONS\n")
    for act in account_repos.keys():
        repos = account_repos[act]
        #  Go through each repo
        for repo in repos:
            #  Clone the github repo into /tmp
            path = clone_git_repo('https://github.com/{}/{}'.format(act, repo))
            if path is None:
                continue
            try:
                #  Search the repo for any reference to the company they work for
                exit_code, _, __ = runcommand("rg {} -i {}".format(COMPANY_NAME, path))
                exit_code2, _, __ = runcommand("rg {} -i {}".format(COMPANY_NAME2, path))
            except UnicodeDecodeError as e:
                print("ERROR: ", act, repo, "UnicodeDecode Error")
                continue
            #  Check if there was a reference to the company
            if exit_code == 0 or exit_code2 == 0:
                print(act, repo)
                with open(out_shhgit, 'a') as f:
                    f.write(act + ' ' + repo + '\n')
                with open(out_trufflehog, 'a') as f:
                    f.write(act + ' ' + repo + '\n')
                #  Search it using shhgit
                os.system("{} --local {} --silent | tee --append {}".format(SHHGIT_PATH, path, out_shhgit))
                #  Search it using truffle hog
                os.system('python3 {} https://github.com/{}/{} --regex --entropy=False | tee --append {}'.format(TRUFFLE_HOG_PATH, act, repo, out_trufflehog))

            #  delete the repo from disk
            shutil.rmtree(path, ignore_errors=True)


def get_usernames_from_html(html_file: str) -> list:
    """
    Takes in a path to a html file. Scrapes the page to find all linkedin accounts
    :param html_file: Path to file
    :return: A list of linkedin usernames
    """
    usernames = []  # LinkedIn Usernames
    if html_file != '' and os.path.isfile(html_file):
        f = open(html_file, 'r')
        soup = BeautifulSoup(f, 'html5lib')
        results = soup.find_all('div', attrs={'class': 'org-people-profile-card'})
        print()
        print('LinkedIn Accounts:')
        print()
        for el in results:
            try:
                link = el.section.div.div.div.a['href']
                full_link_to_linkedin = 'https://www.linkedin.com' + str(link)
                print(full_link_to_linkedin)
                with open('{}.out'.format(FILE_NAME.split('.')[0]), 'a') as fp:
                    fp.write(full_link_to_linkedin + '\n')
                a = str(link).strip("/in/").strip("/")
                usernames.append(urllib.parse.unquote(a))
            except Exception as e:
                pass
        f.close()
        return usernames
    else:
        print('ERROR: File {} Not Found!'.format(html_file))
        exit(1)


def find_unique_usernames(linkedin_usernames: list) -> list:
    """

    :param linkedin_usernames:
    :return:
    """
    unique_linkedin_usernames = []  # If a user makes a custom LinkedIn username

    # Finds unique linkedin usernames
    for i in linkedin_usernames:
        i = urllib.parse.unquote(i)
        if '-' not in i:
            unique_linkedin_usernames.append(i)
    print('Number of accounts: ' + str(len(linkedin_usernames)))
    return unique_linkedin_usernames


def validate_github_accounts(unique_linkedin_usernames: list) -> list:
    """
    Takes in a list of usernames and validates each one using the github API
    :param unique_linkedin_usernames: A list of github usernames
    :return: a list of valid usernames
    """
    valid_accounts = []
    # Goes through the high validity LinkedIn usernames and sees if they exist on Github
    for usr in unique_linkedin_usernames:
        url = 'https://api.github.com/search/users?q=' + str(urllib.parse.quote(usr)) + '&type=Users'
        rl = None
        response = None
        while rl is None or response is None:
            try:
                #  Calculates the amount of time github is rate-limiting us by
                rl = requests.get('https://api.github.com/rate_limit', headers={"Authorization": "Basic {}".format(TOKEN)})
                requests_left = rl.json()['resources']['search']['remaining']
                unlock_epoch = rl.json()['resources']['search']['reset']
                if requests_left == 0:
                    sleep = (int(unlock_epoch) - int(datetime.datetime.now().timestamp())) + 3
                    time.sleep(sleep)
                #  Waits until we aren't rate limited and checks if the user exists
                response = requests.get(url, headers={"Authorization": "Basic {}".format(TOKEN)})
                if not response.ok:
                    print(response, 'You\'re being rate limited by GitHub!')
                json = response.json()
                #  Checks if there is at least 1 user returned
                if json['total_count'] != 0:
                    print()
                    print(usr)
                    #  Grabs the first user
                    print('https://github.com/' + str(json['items'][0]['login']))
                    valid_accounts.append(str(json['items'][0]['login']))
            except Exception as e:
                time.sleep(5)
    return valid_accounts


def check_api_info():
    """
    Checks the API information given at the top of the file
    """
    # Checks your api information
    print('API')
    rl = requests.get('https://api.github.com/rate_limit', headers={"Authorization": "Basic {}".format(TOKEN)})
    print('Limit: ', rl.json()['resources']['search']['limit'])
    print('Remaining: ', rl.json()['resources']['search']['remaining'])
    print()


def find_emails_from_github_username(unique_linkedin_usernames: list):
    """

    :param unique_linkedin_usernames:
    :return:
    """
    print("Finding Account Emails:\n\n")
    os.environ["GH_EMAIL_TOKEN"] = GITHUB_PASSWORD.decode('ascii')
    if os.path.isfile("gitemail.sh"):
        with open('{}.out'.format(FILE_NAME.split('.')[0]), 'a') as fp:
            with open('{}.Emails.out'.format(FILE_NAME.split('.')[0]), 'a') as emails:
                for github_username in unique_linkedin_usernames:
                    returncode, std_out, std_err = runcommand("./gitemail.sh {}".format(github_username))
                    if std_out != "----------@#$%^&*(----------\n":
                        outputs = std_out.split("----------@#$%^&*(----------")
                        if outputs[0] != "":
                            print(github_username + ":")
                            print(outputs[0].strip("\n") + outputs[1])
                        fp.write("\n\n" + github_username + "\n")
                        fp.write(outputs[0] + outputs[1] + "\n")
                        emails.write(outputs[0])
    else:
        print("./gitemail.sh NOT in current directory")


if __name__ == '__main__':
    #  Get the linkedin usernames from the HTML
    linkedin_usernames = get_usernames_from_html(FILE_NAME)
    #  Filter usernames
    unique_linkedin_usernames = find_unique_usernames(linkedin_usernames)
    print()
    print()
    #
    find_emails_from_github_username(unique_linkedin_usernames)
    print()
    print()

    check_api_info()

    print('Github Accounts')
    valid_accounts = validate_github_accounts(unique_linkedin_usernames)
    print('Usernames found: ', len(valid_accounts))

    print()
    print()
    print()

    account_repos = get_repos(valid_accounts)
    print("\n\nHIGH PROBABILITY\n", account_repos)
    print()

    #  Write the dictionary out to the .out file
    with open('{}.out'.format(FILE_NAME.split('.')[0]), 'a') as fp:
        fp.write('HIGH PROBABILITY ACCOUNTS\n\n')
        fp.write(str(account_repos))
        fp.write('\n\n')

    print("\n\n HIGH PROBABILITY ISSUES\n\n")
    find_secrets(account_repos)
