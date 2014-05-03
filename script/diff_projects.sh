#!/bin/bash

PROJECT_1_DIR=$1
PROJECT_2_DIR=$2

PROJECT_PNGS=$(cd $1; find -type f -name "*.png" | sort)

for i in $PROJECT_PNGS; do
    IMAGE_DIFF=$((compare -metric AE $PROJECT_1_DIR/$i $PROJECT_2_DIR/$i /dev/null) 2>&1)
    if [ "$IMAGE_DIFF" != 0 ]
    then
        echo "Files $PROJECT_1_DIR/$i and $PROJECT_2_DIR/$i differ"
    fi
done
diff -r -q $PROJECT_1_DIR $PROJECT_2_DIR | grep -v ".png"