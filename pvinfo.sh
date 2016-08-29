#!/bin/bash

show_help=0
if [[ "$1" ]]; then
  if [[ $1  == '-h' ]]; then
    show_help=1
  elif [[ $1 == '--help' ]]; then
    show_help=1
  fi
fi

args="$@"

SOURCE="${BASH_SOURCE[0]}"
# resolve $SOURCE until the file is no longer a symlink
while [ -h "$SOURCE" ]; do 
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" 
  # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done

DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
cd $DIR

source $DIR/env_setup.sh

python ../pscontrol $args


