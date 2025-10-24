#!/bin/bash

# 拼接数据库路径 "~/Library/Application Support/com.leafmove.leaf-know/sqlite.db"
# 从 tauri.conf.json 读出 "com.leafmove.leaf-know"
identifier=$(cat ../leaf-know/src-tauri/tauri.conf.json | jq -r .identifier)

DB_FOLDER=~/Library/Application\ Support/"$identifier"
# 如果不存在就新建文件夹
if [ ! -d "$DB_FOLDER" ]; then
  mkdir -p "$DB_FOLDER"
fi

DB_PATH="$DB_FOLDER"/sqlite.db
# echo $DB_PATH

uv run main.py \
--port 60000 \
--host 127.0.0.1 \
--db-path "$DB_PATH" \
