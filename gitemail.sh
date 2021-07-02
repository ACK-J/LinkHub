#!/usr/bin/env bash
# Based on: https://gist.github.com/sindresorhus/4512621
# Revised here: https://gist.github.com/cryptostrophe/11234026
# Revised again by me here

user="$1"
repo="$2"

if [ -z $GH_EMAIL_TOKEN ]; then
    echo "   Github requires authenticated API requests to retrieve the email. See: https://git.io/vxctz"
    echo "   To enable, open https://github.com/settings/tokens/new?description=github-email …"
    echo "   Keep the checkboxes unchecked, hit 'Generate token', copy the token, then run this in your shell:"
    echo "       export GH_EMAIL_TOKEN=<token>"
    echo "   You'll also want to add that line to your shell configuration (e.g. .bashrc)"
else
    curl -H "Authorization: token $GH_EMAIL_TOKEN" "https://api.github.com/users/$user" --silent \
        | sed -nE 's#^.*"email": "([^"]+)",.*$#\1#p' | sort -u
fi


if hash jq 2>/dev/null; then
    curl "https://registry.npmjs.org/-/user/org.couchdb.user:$user" -s | jq -r '.email' | sort -u | grep -v "null" 
else
    echo " … skipping …. Please: brew install jq (on OSX) OR apt install jq (on Linux)"
fi

curl -H "Authorization: token $GH_EMAIL_TOKEN" "https://api.github.com/users/$user/events/public" -s \
    | sed -nE 's#^.*"(email)": "([^"]+)",.*$#\2#p' \
    | sort -u

echo "----------@#$%^&*(----------"

if [[ -z $repo ]]; then
    # get all owned repos
    repo="$(curl -H "Authorization: token $GH_EMAIL_TOKEN" "https://api.github.com/users/$user/repos?type=owner&sort=updated" -s \
        | sed -nE 's#^.*"name": "([^"]+)",.*$#\1#p' \
        | head -n1)"
fi


curl -H "Authorization: token $GH_EMAIL_TOKEN" "https://api.github.com/repos/$user/$repo/commits" -s \
    | sed -nE 's#^.*"(email|name)": "([^"]+)",.*$#\2#p'  \
    | pr -2 -at -w 85 \
    | sort -u

