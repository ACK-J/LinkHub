
<p align="center">
<img src="https://user-images.githubusercontent.com/60232273/109367352-d4125a00-7863-11eb-9ca2-1be8ca46d7b5.jpg" width="470" height="405"/>
</p>

---
This program takes in the Html of an organization's employee page on LinkedIn, parses all the profiles, validates the accounts on GitHub, and searches for any security issue in all GitHub repos, leading to information useful for a bug bounty of the original organization.

# Installation
`git clone https://github.com/ACK-J/LinkHub.git`

`cd LinkHub && pip3 install -r requirements.txt && chmod +x gitemail.sh && cd ..`

`sudo apt install jq`

`git clone https://github.com/dxa4481/truffleHog.git`

`go get github.com/eth0izzle/shhgit`

# Tutorial

First, log into https://www.linkedin.com and go to a companies page. I will use Google as an example for this tutorial. 

<p align="center">
<kbd><img src="https://user-images.githubusercontent.com/60232273/109347914-d95ead00-7841-11eb-87e0-25240213d2d3.png" width="732" height="420" /></kbd>
</p>

At the bottom of the header, you will see different tabs. You want to click on `People`.

<p align="center">
<kbd><img src="https://user-images.githubusercontent.com/60232273/109348157-28a4dd80-7842-11eb-967a-6e9c10402cc3.png" width="519" height="419" /></kbd>
</p>

From here you can filter by the type of employee you are looking to find vulnerabilities in. I search for something to the effect of `engineer` since this will include software engineers, security engineers, and other similar development-based jobs. 

<p align="center">
<kbd><img src="https://user-images.githubusercontent.com/60232273/109348572-b1bc1480-7842-11eb-8f03-df826d7aa0f8.png" width="507" height="429" /></kbd>
</p>

For the next part, you need to have a mouse, you can do it without one but it makes the process a lot easier. 

<p align="center">
<kbd><img src="https://user-images.githubusercontent.com/60232273/109348721-eb8d1b00-7842-11eb-85b4-378a332047a3.png" /></kbd>
</p>

`Clicking the center button on a mouse activates "auto-scrolling" where you can move your cursor on the screen and the page will scroll in that direction. This comes in handy since we are going to need to scroll down for a while to see as many employees as possible.`

<p align="center">
<kbd><img src="https://user-images.githubusercontent.com/60232273/109350392-6c4d1680-7845-11eb-87d3-606603f9fc2c.png" width="543" height="421" /></kbd>
</p>

You should see the symbol shown above. Now just move your cursor to the bottom of the screen and it will scroll in that direction until there are no more employees. This most of the time will not return you every single employee that you filtered for, since LinkedIn will eventually limit you but you will be able to capture a few thousand employees in most cases.

## Technical Observations

On the technical side every time you hit the bottom of the page and it loads more users, your browser makes a GET request to 

`https://www.linkedin.com/voyager/api/search/hits?count=12&educationEndYear=List()&educationStartYear=List()&facetCurrentCompany=List(1441,17876832,791962,16140,10440912)&facetCurrentFunction=List()&facetFieldOfStudy=List()&facetGeoRegion=List()&facetNetwork=List()&facetSchool=List()&facetSkillExplicit=List()&keywords=List(engineer)&maxFacetValues=15&origin=organization&q=people&start=108&supportedFacets=List(GEO_REGION,SCHOOL,CURRENT_COMPANY,CURRENT_FUNCTION,FIELD_OF_STUDY,SKILL_EXPLICIT,NETWORK)`

Within this request you can see a few parameters of interest, `count=12` `keywords=List(engineer)` and `q=people`
- By proxying your web requests through Burp Suite and using "match and replace" I was able to increase the speed of this process by changing the count from `12 -> 100`. This way I would be given 100 accounts every time the page refreshed instead of only 12.
- Unfortunately, this did not increase the overall amount of profiles I was able to capture instead just made it go faster. There may be other ways to trick the server into continuously sending more profiles but that is for future research. 

---

Once you have reached the bottom (On Firefox)...
- Right-click on the page
- Select `inspect element`
- Scroll to the top of the "Inspector" tab
<p align="center">
<kbd><img src="https://user-images.githubusercontent.com/60232273/109352909-943e7900-7849-11eb-9f29-2abc40f8ca15.png" /></kbd>
</p>

- Right-click on the `<html>` tag shown above
- Go to `Copy -> Outer HTML`
- Paste the contents into a text file and save it as something like `google.html`

## Configuring linkhub.py
Now that you have your `HTML` file ready to go you're going to need to configure only a few global variables within the linkhub.py file. Don't worry this will be super quick and easy. 

When you open the file it should look similar to this.

<p align="center">
<kbd><img src="https://user-images.githubusercontent.com/60232273/109353767-d1efd180-784a-11eb-919e-c2c80e5ded09.png" width="475" height="313"/></kbd>
</p>

The GitHub username and API-token (password) are needed to hit the GitHub API. If you don't already have a Github API token you can generate one by going to `https://github.com/settings/tokens` and clicking `"Personal Access Token" -> "Generate New Token"`. 
- You do not need to give the token any permissions!

Next, give the full paths to the `trufflehog.py` script and the `sshgit` binary.

Put the `HTML` file we saved before within the LinkHub folder and provide the file name to the global variable `FILE_NAME`.

Lastly, give two search terms that should be used to look for within each GitHub repo which may indicate it is used at the company. 
- Normally I put the name of the company and a subsidiary of the company.

<p align="center">
<kbd><img src="https://user-images.githubusercontent.com/60232273/109355253-f64cad80-784c-11eb-8606-60ff5ebedf25.png" width="475" height="313" /></kbd>
</p>

## Run the program!
`python3 linkhub.py`

## Notes
If you want to find the email address of a GitHub user you can use the following command and substitute the API key and the username.

`GH_EMAIL_TOKEN=01234567890123456789 ./gitemail.sh ACK-J`

## Thoughts
What makes this technique possible is the over-abundance of specific user-data LinkedIn is willing to share with anyone with an account. LinkedIn most of the time will let you see over 1,000 employee accounts before it cuts you off. There are cases where you will not be able to see the employee's LinkedIn account, this is because you are most likely not within 3+ connections. You can simply fix this by connecting with a few people at a single company. A good privacy option that would stop this technique is allowing users to only share their profile with their immediate connections and making anyone else have to request access.
