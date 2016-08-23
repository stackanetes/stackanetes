#!/bin/sh

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

set -e

GEN_CMD=oslo-config-generator

if ! type -p "$GEN_CMD" > /dev/null ; then
    echo "ERROR: $GEN_CMD not installed on the system."
    exit 1
fi

for file in `ls etc/oslo-config-generator/*`; do
    $GEN_CMD --config-file=$file
done

if [ ! -d /etc/stackanetes ]
then
    mkdir /etc/stackanetes
fi

if [ ! -f /etc/stackanetes/globals.yml ]
then
    cp etc/globals.yml /etc/stackanetes/globals.yml
fi

if  [ ! -f /etc/stackanetes/stackanetes.conf ]
then
     cp etc/stackanetes.conf.sample /etc/stackanetes/stackanetes.conf
     # Sometimes OS (especially lightweight OS) doesn't have uuidgen binary.
     # That's why we use python uuid generator.
     X=`python -c "import uuid; print uuid.uuid4()"`
     sed -i "s@#uuid =@uuid = $X@g" /etc/stackanetes/stackanetes.conf
fi

if [ ! -f /etc/stackanetes/passwords.yml ]
then
    cp etc/passwords.yml /etc/stackanetes/passwords.yml
fi

set -x
