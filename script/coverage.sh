#!/bin/sh

nosetests --with-cov --cov-report html --cov coilsnake tests
xdg-open ./build/coverage_html/index.html
