import requests, datetime, time, os, urllib, re, subprocess

start_time = time.time()
# Set your GitHub authentication token
auth_token = 'YOUR_ACCESS_TOKEN'

# Define the API endpoint and parameters
# Parameters defined to search for the 1000 repositories with the most stars, that have at least 4000 forks
url = 'https://api.github.com/search/repositories'
params = {'q': 'stars:>10000', 'sort': 'stars', 'order': 'desc', 'forks':'>4000', "per_page":"100", "page":"1"}
params2 = {'q': 'stars:>10000', 'sort': 'stars', 'order': 'desc', 'forks':'>4000', "per_page":"100", "page":"2"}
params3 = {'q': 'stars:>10000', 'sort': 'stars', 'order': 'desc', 'forks':'>4000', "per_page":"100", "page":"3"}
params4 = {'q': 'stars:>10000', 'sort': 'stars', 'order': 'desc', 'forks':'>4000', "per_page":"100", "page":"4"}
params5 = {'q': 'stars:>10000', 'sort': 'stars', 'order': 'desc', 'forks':'>4000', "per_page":"100", "page":"5"}
params6 = {'q': 'stars:>10000', 'sort': 'stars', 'order': 'desc', 'forks':'>4000', "per_page":"100", "page":"6"}
params7 = {'q': 'stars:>10000', 'sort': 'stars', 'order': 'desc', 'forks':'>4000', "per_page":"100", "page":"7"}
params8 = {'q': 'stars:>10000', 'sort': 'stars', 'order': 'desc', 'forks':'>4000', "per_page":"100", "page":"8"}
params9 = {'q': 'stars:>10000', 'sort': 'stars', 'order': 'desc', 'forks':'>4000', "per_page":"100", "page":"9"}
params10 = {'q': 'stars:>10000', 'sort': 'stars', 'order': 'desc', 'forks':'>4000', "per_page":"100", "page":"10"}
# Set the authentication header with your token
headers = {'Authorization': f'token {auth_token}'}
responses = []
# Send the request to the API with authentication headers
response = requests.get(url, params=params, headers=headers)
response2 = requests.get(url, params=params2, headers=headers)
response3 = requests.get(url, params=params3, headers=headers)
response4 = requests.get(url, params=params4, headers=headers)
response5 = requests.get(url, params=params5, headers=headers)
response6 = requests.get(url, params=params6, headers=headers)
response7= requests.get(url, params=params7, headers=headers)
response8 = requests.get(url, params=params8, headers=headers)
response9 = requests.get(url, params=params9, headers=headers)
response10 = requests.get(url, params=params10, headers=headers)
responses.extend([response, response2, response3, response4, response5, response6, response7, response8, response9, response10])

# Create a list for the repos from requests
repositories= []
# Create a list that will contain the repositories the repositories with more than 50000 commits 
filtered_repos= []
# Create a list that will contain the repositories the repositories that should be mined
final_repos = []
# create a list to show where the repo was found( position 1, 2, ..., 1000)
indexes= []
final_indexes= []
for response in responses:
    # Check if the  request was successful
    if response.status_code == 200:
        # Parse the JSON response into a Python dictionary
        data = response.json()
        # Extract the list of repositories from the dictionary
        repositories += data['items']
    else:
        print(f"Error: {response.status_code}")

# Print the name and number of stars for each repository
i=0
for repo in repositories:
    print(f"{i} {repo['name']}: {repo['stargazers_count']} stars")
    i=i+1    

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
                                                                
# Appends all the repositories with first commit before 2004 and 
# more than 50000 commits to the final_repos list
i = 0
for repo in repositories:
    # Get the masters' sha in order to find the number of commits
    repo_url = 'https://github.com/' + repo['full_name']
    process = subprocess.Popen(["git", "ls-remote", repo_url], stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    sha = re.split(r'\t+', stdout.decode('utf-8'))[0]
    commit_number = commit_count(repo['full_name'], sha, auth_token)
    if commit_number > 50000:
        filtered_repos.append(repo)
        indexes.append(i)
    i = i + 1
i=0
for repo in filtered_repos:   
    year = get_contributors_years(repo['owner']['login'], repo['name'])
    if year < datetime.datetime(2004, 1, 1):
        final_repos.append(repo)
        print(f"{repo['owner']['login']}/{repo['name']}: {repo['stargazers_count']} stars")
        final_indexes.append(indexes[i])
    i += 1  
end_time = time.time()
execution_time = end_time - start_time
print(execution_time)
print(final_indexes)

