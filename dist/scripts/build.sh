#!/bin/bash


# A very simple bash script to create a release.

VERSION="0.5"

DISTDIR="/var/tmp/sct"
DISTNAME="sct-$VERSION"
SVNDIR="trunk"


rm -rf "$DISTDIR"
mkdir -p "$DISTDIR/$DISTNAME"
cd "$DISTDIR/$DISTNAME"

svn export http://yourhell.com/svn/root/django/communitytools/$SVNDIR communitytools >> tmp
svn export http://yourhell.com/svn/root/django/communitydraft/$SVNDIR communitydraft >> tmp

revision=`cat tmp |grep revision -m 1 | sed "s/.* \([0-9]\+\).*/\1/"`

rm tmp

cat <<EOF >> BUILD
SVN Revision: $revision
SVN Dir: $SVNDIR
Date: `date`
Version: $VERSION
Name: $DISTNAME
EOF

cp -fr communitytools/dist/files/* .
cp communitytools/LICENSE .
cp communitytools/AUTHORS .

wget -O communitydraft/README "http://sct.sphene.net/wiki/show/CommunityDraft/?type=src" 2> /dev/null

cd ..

tar -czf "$DISTNAME.tar.gz" "$DISTNAME"

rm -rf "$DISTNAME"

echo "Created file $DISTDIR/$DISTNAME.tar.gz"

