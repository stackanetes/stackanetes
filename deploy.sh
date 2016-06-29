#!/bin/bash
python setup.py install
stackanetes --config-dir /etc/stackanetes --debug kill $1
stackanetes --config-dir /etc/stackanetes --debug run $1
