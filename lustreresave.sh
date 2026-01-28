#!/bin/bash

# --------------------------------
# Lustre quota → JSON → upsert
# --------------------------------

# 1. 获取真实 Lustre quota（去掉表头）
quota_output=$(lfs quota -uah | awk 'NR>2')

# 2. 逐行发送
while read -r line; do
    [[ -z "$line" ]] && continue

    # 按空格拆列
    read -ra cols <<< "$line"

    # 防御性判断（避免列不够）
    [[ ${#cols[@]} -lt 7 ]] && continue

    # 构建 JSON（与你接口字段严格对应）
    json_obj=$(jq -n \
        --arg iphone "${cols[0]}" \
        --arg id "${cols[1]}" \
        --arg name "${cols[2]}" \
        --arg address "${cols[6]}" \
        '{id:$id, name:$name, address:$address, iphone:$iphone}')

    # PUT 到 upsert 接口
    curl -s -X PUT \
        -H "Content-Type: application/json" \
        -d "$json_obj" \
        http://127.0.0.1:8000/api/resave

    echo "Sent: $json_obj"
done <<< "$quota_output"

