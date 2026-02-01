#!/bin/bash

# 手动输入参数一次性设置 quota 并同步数据库
# 输入格式:  name iphone

name2="$1"
address2="$2"

# Lustre quota → JSON → upsert
quota_output=$(lfs quota -uah | awk 'NR>2' | grep "$name2")
CLUSTER_ID=9654

while read -r line; do
    [[ -z "$line" ]] && continue

    # 拆列
    read -ra cols <<< "$line"
    [[ ${#cols[@]} -lt 4 ]] && continue

    filesystem="${cols[0]}"   # /opt/phadcloud/lustre
    user_or_id="${cols[1]}"   # quota_id 或用户名
    num="${cols[2]}"           # 第3列
    iphone="${cols[3]}"        # 第4列

    # 判断是数字还是用户名
    if [[ "$user_or_id" =~ ^[0-9]+$ ]]; then
        id="$user_or_id"
        name="$user_or_id"
        # 数字 UID 用户，用 $HOME
        address="$HOME"
    else
        name="$user_or_id"
        id=$(id -u "$name" 2>/dev/null || echo 0)
        # 查询 home 目录
        home_dir=$(getent passwd "$name" | cut -d: -f6)
        [[ -z "$home_dir" ]] && home_dir="$HOME"
        address="$home_dir"
    fi

    # 构建 JSON
    json_obj=$(jq -n \
        --argjson id "$id" \
        --arg name "$name" \
        --arg address "$address" \
        --arg num "$num" \
        --arg iphone "$iphone" \
        --arg cluster_id "$CLUSTER_ID" \
        '{
            id: $id,
            name: $name,
            address: $address,
            num: $num,
            iphone: $iphone,
            cluster_id: $cluster_id
        }')

    # PUT 到接口
    response=$(curl -s -o /dev/null -w "%{http_code}" -X PUT \
        -H "Content-Type: application/json" \
        -d "$json_obj" \
        http://10.82.4.120:8000/api/resave)

    echo "Sent: $json_obj | HTTP: $response"

done <<< "$quota_output"