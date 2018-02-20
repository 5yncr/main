#!/bin/bash

# This script tries to pull in changes from the repos listed in .repos to
#  commits in subdirectories here.  It will also generate a changelog, per
#  author, based on commit logs

for repo in $(cat .repos); do
    dest=$(basename $repo)
    tmpdir=$(mktemp -d)
    curdir=$(pwd)
    if [[ ! -d ./$dest ]]; then
        echo "Making $dest"
        mkdir $dest
    fi
    echo "updating from $repo to $dest/, tmpdir: $tmpdir"
    # The last commit for this repo that's been included should end with
    #  "Original commit: $dest $hash"
    lastcommit=$(
        git log | grep "Original commit: $dest" | awk '{ print $4 }' | head -n1
    )
    # If this is the first commit, don't use a range, otherwise then to HEAD
    if [[ $lastcommit = "" ]]; then
        range=""
    else
        range="$lastcommit..HEAD"
    fi

    git clone $repo $tmpdir
    pushd $tmpdir
    for commit in $(git log --pretty=format:"%H" $range --reverse); do
        # This is the patch from a commit
        p="$(git format-patch -1 $commit --stdout)"
        author="$(git log --format=%an $commit -n1)"
        email="$(git log --format=%ae $commit -n1)"
        d="$(git log --format=%at $commit -n1)"
        message="$(git log --format=%B $commit -n1)"
        pushd ${curdir}/${dest}
        # Here we apply the patch from the commit
        echo "$p" | patch -p1
        git add .
        # And keep as much info as possible, as well as the original commit id
        printf "$dest: $message\n\n\nOriginal commit: $dest $commit" | \
            git commit --author="$author <$email>" --date="$d" -F -
        popd
    done
    popd

    echo "cleaning up $tmpdir"
    rm -rf $tmpdir
done

# This should find last week's weekly commit; we'll want a shortlog since then
lastcommit=$(
    git log --grep "Weekly commit" | grep "commit " | awk '{ print $2 }' | head -n1
)
# shortlog needs a range ("HEAD" seems to be biginning of time until HEAD)
if [[ $lastcommit = "" ]]; then
    range="HEAD"
else
    range="$lastcommit..HEAD"
fi
# Find all authors (maybe should only be since last week?)
authors=$(git shortlog --no-merges -sn | sed 's/^.*[0-9]\t//')
d=$(date +%d/%m/%Y)

while read -r a; do
    if [[ ! $a = "CommitBot" ]]; then
        filename="README.$a"
        touch "$filename"
        mv "$filename" "$filename.old"
        echo "# $d" >> "$filename"
        # The changelog is just a shortlog for that author
        git shortlog --no-merges --author="$a" $range | grep -v "$a" >> "$filename"
        cat "$filename.old" >> "$filename"
        rm "$filename.old"
    fi
done <<< $authors

mv README.md README.md.old
echo "# $d" > README.md
echo "      " >> README.md
printf '\n\n' >> README.md
cat README.md.old >> README.md
rm README.md.old

read -p "Now make any necessary changes to README.* files. Press enter to continue"
git add .
git commit --author="CommitBot <commitbot@mtb.wtf>" -m "Weekly commit"
