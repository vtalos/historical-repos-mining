import requests, datetime, time, os, urllib, re, subprocess, calendar

# Count the number of commits in 'master' branch
def commit_count(project, sha='master', token=None):

    # PAT
    token = token or os.environ.get('GITHUB_API_TOKEN')

   # project commits url
    url = f'https://api.github.com/repos/{project}/commits'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'token {token}',
    }
    params = {
        'sha': sha,
        'per_page': 1, # 1 page per commit
    }
    resp = requests.request('GET', url, params=params, headers=headers)
    if (resp.status_code // 100) != 2:
        raise Exception(f'invalid github response: {resp.content}')
    # check the resp count, just in case there are 0 commits
    commit_count = len(resp.json())
    last_page = resp.links.get('last')
    # if there are no more pages, the count must be 0 or 1
    if last_page:
        # extract the query string from the last page url
        qs = urllib.parse.urlparse(last_page['url']).query
        # extract the page number from the query string
        commit_count = int(dict(urllib.parse.parse_qsl(qs))['page']) # Get the number of commits by the last page
    return commit_count

def enough_contributors(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/stats/contributors"

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)

    # Redo the request, so the status code 202 may change to 200.
    # Don't do the request more than 4 times
    j = 0
    while response.status_code == 202 and j <= 4:
        time.sleep(5)
        response = requests.get(url, headers=headers)
        j = + 1

    contributors = []
    page = 1
    per_page = 100

    while True:
        params = {"page": page, "per_page": per_page}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            contributors += response.json()
            if page > 2:
                return True
            if len(response.json()) < per_page:
                break
            page += 1
            time.sleep(1)
        else:
            print("Failed to retrieve contributors:", response.status_code)
            break
    return False

def monthly_commit_count(project, sha='master', token=None):

    # PAT
    token = token or os.environ.get('GITHUB_API_TOKEN')

   # project commits url
    url = f'https://api.github.com/repos/{project}/commits'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'token {token}',
    }
    params = {
        'sha': sha,
        'per_page': 1, # 1 page per commit
    }
    years=list(range(2004,2023))
    months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    per_month = 1 # Count commits per one month
    not_dense = 0 # The number of months that have under 100 commits
    for year in years:
        for month in months:
            start_date = datetime.datetime(int(year), int(month), 1)
            params['since'] = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            _, days_in_month = calendar.monthrange(year, month)
            end_date = start_date + datetime.timedelta(days_in_month)
            params['until'] = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

            resp = requests.request('GET', url, params=params, headers=headers)

            if (resp.status_code // 100) != 2:
                raise Exception(f'invalid github response: {resp.content}')
            # check the resp count, just in case there are 0 commits
            commit_count = len(resp.json())
            last_page = resp.links.get('last')
            # if there are no more pages, the count must be 0 or 1
            if last_page:
                # extract the query string from the last page url
                qs = urllib.parse.urlparse(last_page['url']).query
                # extract the page number from the query string
                commit_count = int(dict(urllib.parse.parse_qsl(qs))['page'])  # Get the number of commits by the last page
            if commit_count < 100:
                not_dense = not_dense + 1 # if this month has under 100 commits, increase the not_dence months by one
    return not_dense


# returns the date of the first commit of the repo, taking as input it's owner and it's name.
def get_contributors_years(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/stats/contributors"

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)

    #Redo the request, so the status code 202 may change to 200.
    #Don't do the request more than 4 times
    j=0
    while response.status_code == 202 and j<=4:
        time.sleep(5)
        response=requests.get(url, headers=headers)
        j =+ 1

    if response.status_code == 200:
        contributors = response.json()
        #retrieves the data of the first commit in the repo

        for contributor in contributors:
            weeks = contributor["weeks"]
            first_week = weeks[0]
            first_commit_date = datetime.datetime.fromtimestamp(first_week["w"])
        return first_commit_date
    
    if response.status_code == 202:
        print("Status code 202")
        # Returns March 18, 2022. It is a random date that will not fit 
        # the condition in order to be appended to the filtered_repos list
        return datetime.datetime.fromtimestamp(1647768000)   

start_time = time.time()
# Set your GitHub authentication token
auth_token = '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'
repositories = []
filtered_repos = []
final_repos = []

# set the search query and parameters
query = "stars:>100 forks:>100"
sort = "stars"
order = "desc"
per_page = 100
page = 1
headers = {"Accept": "application/vnd.github.v3+json"}

# loop through all pages of results and add the name of each repository to the list
while True:
    # make a request to the GitHub API with the specified parameters and pagination
    url = f"https://api.github.com/search/repositories?q={query}&sort={sort}&order={order}&per_page={per_page}&page={page}"
    response = requests.get(url, headers=headers)
    # check if there are no more results and break out of the loop
    if "items" not in response.json() or len(response.json()["items"]) == 0:
        break
    # parse the response to get the names of the repositories and add them to the list
    repos = response.json()["items"]
    for repo in repos:
        repositories.append(repo)
        print(f" {repo['name']}: {repo['stargazers_count']} stars")
    # increment the page number to retrieve the next page of results
    page += 1
    
# Appends all the repositories with first commit before 2004, more than 200 contributors,
# at least 100 commits per month and more than 50000 commits to the final_repos list

for repo in repositories:
    # Get the masters' sha in order to find the number of commits
    repo_url = 'https://github.com/' + repo['full_name']
    process = subprocess.Popen(["git", "ls-remote", repo_url], stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    sha = re.split(r'\t+', stdout.decode('utf-8'))[0]
    commit_number = commit_count(repo['full_name'], sha, auth_token)
    if commit_number > 50000 :
        filtered_repos.append(repo)
    
for repo in filtered_repos:
    repo_url = 'https://github.com/' + repo['full_name']
    process = subprocess.Popen(["git", "ls-remote", repo_url], stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    sha = re.split(r'\t+', stdout.decode('utf-8'))[0]
    year = get_contributors_years(repo['owner']['login'], repo['name'])
    if year < datetime.datetime(2004, 1, 1) and enough_contributors(repo['owner']['login'], repo['name']) :
        if monthly_commit_count(repo['full_name'], sha, auth_token) < 15 :
            final_repos.append(repo['full_name'])
            print(f"{repo['owner']['login']}/{repo['name']}: {repo['stargazers_count']} stars")
             
end_time = time.time()
print(final_repos)
execution_time = end_time - start_time
print(execution_time)
