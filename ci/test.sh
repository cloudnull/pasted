#!/bin/bash
set -ex

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR/../

export GOPATH="$HOME/go/"

# Install dependencies.
go get google.golang.org/appengine

# Run unit tests.
go test

# Run App Engine tests.
goapp test
